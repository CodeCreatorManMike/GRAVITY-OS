# voice.py — wake-word detection, audio capture, voice pipeline
#
# Pipeline:
#   1. Continuous I2S read from ICS-43434 mic
#   2. Wake word detection:
#        - Primary:  esp_sr native module (if compiled into this firmware build)
#        - Fallback: energy-threshold (RMS > threshold for N consecutive frames)
#   3. Record RECORD_SECONDS of audio after wake
#   4. HTTP POST raw PCM to backend /voice/process
#   5. Parse JSON response → extract transcript + action + TTS audio (base64 WAV)
#   6. Play TTS response on MAX98357A via I2S output
#
# Key constraints (from build context):
#   - Device is dumb terminal — no AI logic here, just capture + relay
#   - Never stream audio continuously (wake-word gate enforced)
#   - Always wake-word triggered; no push-to-touch
#
# Config pins (config.py): I2S_BCLK=1, I2S_WS=2, I2S_DIN=42, I2S_DOUT=41

import machine
import utime
import ubinascii
import ujson
import usocket
import struct
import config

# ── Constants ──────────────────────────────────────────────────────────────────

SAMPLE_RATE    = 16000    # Hz — matches faster-whisper default
SAMPLE_BITS    = 16
CHANNELS       = 1        # mono
RECORD_SECONDS = 5        # seconds to capture after wake word

# Energy-threshold wake detection
WAKE_FRAME_SAMPLES  = 512          # samples per analysis frame
WAKE_THRESHOLD_RMS  = 800          # 0-32767 scale; tune after hardware arrives
WAKE_TRIGGER_FRAMES = 3            # consecutive hot frames before wake fires

# I2S buffer
_I2S_BUF_SAMPLES = 1024
_I2S_BUF_BYTES   = _I2S_BUF_SAMPLES * 2   # 16-bit


# ── ESP-SR helper (optional native module) ────────────────────────────────────

_esp_sr = None

def _try_load_esp_sr():
    global _esp_sr
    try:
        import esp_sr                  # noqa: F401 — only available on custom builds
        _esp_sr = esp_sr
        print("[voice] esp_sr native module loaded")
    except ImportError:
        print("[voice] esp_sr not available — using energy-threshold wake word")


# ── RMS energy calculation ────────────────────────────────────────────────────

def _rms(buf_bytes):
    """Calculate RMS of 16-bit signed PCM buffer."""
    n      = len(buf_bytes) // 2
    if n == 0:
        return 0
    total  = 0
    for i in range(n):
        sample = struct.unpack_from("<h", buf_bytes, i * 2)[0]
        total += sample * sample
    return int((total // n) ** 0.5)


# ── HTTP multipart POST (minimal, no external libs) ──────────────────────────

def _http_post_audio(pcm_bytes, token):
    """
    POST raw PCM as multipart/form-data to POST /voice/process.
    Returns parsed JSON dict or None on error.
    """
    boundary  = b"GravityAudioBoundary"
    host      = config.BACKEND_HOST
    port      = config.BACKEND_PORT
    path      = "/voice/process"

    # Build multipart body
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Disposition: form-data; name=\"file\"; filename=\"audio.pcm\"\r\n"
        b"Content-Type: audio/pcm\r\n\r\n"
        + pcm_bytes
        + b"\r\n--" + boundary + b"--\r\n"
    )

    headers = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Authorization: Bearer {token}\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary.decode()}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode()

    try:
        addr = usocket.getaddrinfo(host, port)[0][-1]
        sock = usocket.socket()
        sock.settimeout(15)
        sock.connect(addr)
        sock.write(headers)
        # Send body in chunks to avoid MicroPython memory pressure
        chunk = 4096
        offset = 0
        while offset < len(body):
            sock.write(body[offset:offset + chunk])
            offset += chunk

        # Read response
        response = b""
        while True:
            chunk_data = sock.read(2048)
            if not chunk_data:
                break
            response += chunk_data
        sock.close()

        # Split headers from body
        if b"\r\n\r\n" not in response:
            print("[voice] malformed HTTP response")
            return None

        resp_headers, resp_body = response.split(b"\r\n\r\n", 1)
        headers_str = resp_headers.decode("utf-8", "ignore")

        # Extract X-Audio-Base64 header for TTS
        audio_b64 = None
        for line in headers_str.split("\r\n"):
            if line.lower().startswith("x-audio-base64:"):
                audio_b64 = line.split(":", 1)[1].strip()
                break

        # Parse JSON body
        result = ujson.loads(resp_body)
        if audio_b64:
            result["_tts_b64"] = audio_b64
        return result

    except Exception as e:
        print(f"[voice] HTTP POST error: {e}")
        return None


# ── I2S TTS playback ──────────────────────────────────────────────────────────

def _play_tts(wav_b64):
    """
    Decode base64 WAV and play via I2S output to MAX98357A.
    Skips WAV header (44 bytes) and streams raw PCM.
    """
    try:
        wav_bytes = ubinascii.a2b_base64(wav_b64)
    except Exception as e:
        print(f"[voice] base64 decode error: {e}")
        return

    # Skip 44-byte WAV header (standard PCM WAV)
    pcm_start = 44
    if len(wav_bytes) <= pcm_start:
        print("[voice] WAV too short")
        return

    try:
        i2s_out = machine.I2S(
            1,
            sck=machine.Pin(config.I2S_BCLK),
            ws=machine.Pin(config.I2S_WS),
            sd=machine.Pin(config.I2S_DOUT),
            mode=machine.I2S.TX,
            bits=16,
            format=machine.I2S.MONO,
            rate=22050,          # edge-tts default output rate
            ibuf=8192,
        )
        pcm = wav_bytes[pcm_start:]
        chunk_size = 4096
        offset = 0
        while offset < len(pcm):
            written = i2s_out.write(pcm[offset:offset + chunk_size])
            offset += written
        # Drain
        utime.sleep_ms(200)
        i2s_out.deinit()
        print("[voice] TTS playback complete")
    except Exception as e:
        print(f"[voice] I2S playback error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# VoiceManager
# ══════════════════════════════════════════════════════════════════════════════

class VoiceManager:
    """
    Owns the I2S microphone and wake-word detection loop.

    Usage (from main.py):
        vm = VoiceManager(ws_client, cache_module)
        vm.start()           # initialise I2S
        # In main loop:
        vm.poll()            # non-blocking check; fires pipeline when wake detected
    """

    def __init__(self, ws_client, cache_mod):
        self._ws          = ws_client
        self._cache       = cache_mod
        self._i2s_rx      = None
        self._buf         = bytearray(_I2S_BUF_BYTES)
        self._hot_frames  = 0       # consecutive frames above threshold
        self._recording   = False
        self._record_buf  = bytearray()
        self._record_start_ms = 0
        self._esp_sr_model = None
        self._enabled     = True

    def start(self):
        """Initialise I2S receive from ICS-43434 mic."""
        _try_load_esp_sr()
        if _esp_sr:
            self._esp_sr_model = self._init_esp_sr()

        try:
            self._i2s_rx = machine.I2S(
                0,
                sck=machine.Pin(config.I2S_BCLK),
                ws=machine.Pin(config.I2S_WS),
                sd=machine.Pin(config.I2S_DIN),
                mode=machine.I2S.RX,
                bits=SAMPLE_BITS,
                format=machine.I2S.MONO,
                rate=SAMPLE_RATE,
                ibuf=8192,
            )
            print("[voice] I2S microphone initialised")
        except Exception as e:
            print(f"[voice] I2S init error: {e}")
            self._i2s_rx = None

    def stop(self):
        if self._i2s_rx:
            self._i2s_rx.deinit()
            self._i2s_rx = None

    def enable(self, on):
        """App can disable voice (ambient mode off)."""
        self._enabled = on

    def poll(self):
        """
        Non-blocking. Call every main-loop iteration.
        Returns True if a voice action was fired this tick.
        """
        if not self._enabled or self._i2s_rx is None:
            return False

        # Non-blocking read — try to get a frame
        try:
            n = self._i2s_rx.readinto(self._buf, timeout=0)
        except Exception:
            return False
        if n == 0:
            return False

        frame = self._buf[:n]

        if self._recording:
            return self._handle_recording(frame)
        else:
            return self._handle_wake_detection(frame)

    # ── Wake detection ────────────────────────────────────────────────────────

    def _init_esp_sr(self):
        try:
            model = _esp_sr.WakeNet()
            model.load("hilexin7q8")   # 'Hey Gravity' best approximation until custom model
            print("[voice] esp_sr WakeNet loaded: hilexin7q8")
            return model
        except Exception as e:
            print(f"[voice] esp_sr model load failed: {e}")
            return None

    def _handle_wake_detection(self, frame):
        woke = False

        # ESP-SR path
        if self._esp_sr_model:
            try:
                result = self._esp_sr_model.detect(frame)
                if result > 0:
                    woke = True
                    print("[voice] esp_sr wake word detected")
            except Exception:
                pass

        # Energy-threshold fallback
        if not woke:
            rms = _rms(frame)
            if rms > WAKE_THRESHOLD_RMS:
                self._hot_frames += 1
                if self._hot_frames >= WAKE_TRIGGER_FRAMES:
                    woke = True
                    print(f"[voice] energy wake detected (rms={rms})")
            else:
                self._hot_frames = max(0, self._hot_frames - 1)

        if woke:
            self._hot_frames    = 0
            self._recording     = True
            self._record_buf    = bytearray(frame)   # include triggering frame
            self._record_start_ms = utime.ticks_ms()
            print("[voice] recording started")

        return False

    def _handle_recording(self, frame):
        self._record_buf += frame
        elapsed_ms = utime.ticks_diff(utime.ticks_ms(), self._record_start_ms)

        if elapsed_ms < RECORD_SECONDS * 1000:
            return False   # still recording

        # Recording complete — fire pipeline
        print(f"[voice] recording done: {len(self._record_buf)} bytes")
        self._recording = False
        audio = bytes(self._record_buf)
        self._record_buf = bytearray()
        self._fire_pipeline(audio)
        return True

    # ── Voice pipeline ────────────────────────────────────────────────────────

    def _fire_pipeline(self, pcm_bytes):
        """Send audio to backend, apply response, play TTS."""
        token = self._cache.load_jwt()
        if not token:
            print("[voice] no JWT — skipping pipeline")
            return

        print("[voice] sending audio to backend ...")
        result = _http_post_audio(pcm_bytes, token)
        if not result:
            print("[voice] no response from backend")
            return

        transcript = result.get("transcript", "")
        action     = result.get("action", {})
        tts_b64    = result.get("_tts_b64")

        print(f"[voice] transcript: {transcript}")
        print(f"[voice] action: {action}")

        # Notify backend via WebSocket so other devices/app also update
        if self._ws and self._ws.is_connected():
            self._ws.send_event("VOICE_ACTION", {
                "transcript": transcript,
                "action":     action,
            })

        # Play TTS response on speaker
        if tts_b64:
            print("[voice] playing TTS response ...")
            _play_tts(tts_b64)
        else:
            print("[voice] no TTS audio in response")
