# websocket_client.py — persistent WebSocket connection, event dispatch, auto-reconnect
#
# Implements a minimal RFC 6455 WebSocket client over raw sockets.
# MicroPython does not ship a WS library, so we roll our own.
# Only text frames are used (GRAVITY backend sends/receives JSON).

import usocket
import ussl
import ubinascii
import uos
import ujson
import utime
import struct
import config

# ── Constants ─────────────────────────────────────────────────────────────────
_WS_MAGIC   = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_OP_CONT    = 0x0
_OP_TEXT    = 0x1
_OP_BINARY  = 0x2
_OP_CLOSE   = 0x8
_OP_PING    = 0x9
_OP_PONG    = 0xA

_RECONNECT_BASE_MS = 2_000
_RECONNECT_MAX_MS  = 60_000


def _handshake_key():
    raw = uos.urandom(16)
    return ubinascii.b2a_base64(raw).strip()


def _build_http_upgrade(host, path, key, token):
    lines = [
        f"GET {path} HTTP/1.1",
        f"Host: {host}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {key.decode()}",
        "Sec-WebSocket-Version: 13",
    ]
    if token:
        lines.append(f"Authorization: Bearer {token}")
    lines.append("\r\n")
    return "\r\n".join(lines).encode()


def _read_http_response(sock):
    """Read HTTP response headers line by line, return status line."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.read(1)
        if not chunk:
            break
        buf += chunk
    return buf


def _mask_payload(payload):
    mask = uos.urandom(4)
    masked = bytearray(len(payload))
    for i, b in enumerate(payload):
        masked[i] = b ^ mask[i % 4]
    return mask, masked


def _build_frame(opcode, payload, fin=True):
    """Build a masked client→server WebSocket frame."""
    header = bytearray()
    b0 = (0x80 if fin else 0x00) | (opcode & 0x0F)
    header.append(b0)
    plen = len(payload)
    if plen <= 125:
        header.append(0x80 | plen)
    elif plen <= 65535:
        header.append(0x80 | 126)
        header += struct.pack(">H", plen)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", plen)
    mask, masked_payload = _mask_payload(payload if isinstance(payload, (bytes, bytearray)) else payload.encode())
    return bytes(header) + bytes(mask) + bytes(masked_payload)


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.read(n - len(buf))
        if not chunk:
            raise OSError("socket closed")
        buf += chunk
    return buf


class WebSocketClient:
    """
    Minimal WebSocket client for MicroPython.

    Usage:
        ws = WebSocketClient()
        ws.register("LAYOUT_UPDATE", handler_fn)
        ws.connect()
        while True:
            ws.poll()        # non-blocking, call in main loop
            utime.sleep_ms(50)
    """

    def __init__(self):
        self._sock = None
        self._handlers = {}
        self._connected = False
        self._last_reconnect_ms = 0
        self._reconnect_delay = _RECONNECT_BASE_MS
        self._token = None

    # ── Public API ────────────────────────────────────────────────────────────

    def set_token(self, token):
        self._token = token

    def register(self, event_name, handler):
        """Register a callable for a named event type."""
        self._handlers[event_name] = handler

    def connect(self):
        """
        Attempt a WebSocket handshake.
        Returns True on success. Does not block on failure.
        """
        try:
            self._close_socket()
            host = config.BACKEND_HOST
            port = config.BACKEND_PORT
            user_id = config.USER_ID
            path = config.BACKEND_WS_PATH.format(user_id=user_id)
            if self._token:
                path += f"?token={self._token}"

            print(f"[ws] connecting to ws://{host}:{port}{path}")
            addr = usocket.getaddrinfo(host, port)[0][-1]
            sock = usocket.socket()
            sock.connect(addr)
            sock.setblocking(False)

            key = _handshake_key()
            sock.setblocking(True)
            sock.write(_build_http_upgrade(f"{host}:{port}", path, key, self._token))
            resp = _read_http_response(sock)
            if b"101" not in resp:
                print(f"[ws] handshake rejected: {resp[:80]}")
                sock.close()
                return False

            sock.setblocking(False)
            self._sock = sock
            self._connected = True
            self._reconnect_delay = _RECONNECT_BASE_MS
            print("[ws] connected")
            return True

        except Exception as e:
            print(f"[ws] connect error: {e}")
            self._connected = False
            return False

    def poll(self):
        """
        Non-blocking poll. Call every loop iteration.
        Dispatches any received frames and handles auto-reconnect.
        """
        if not self._connected:
            now = utime.ticks_ms()
            if utime.ticks_diff(now, self._last_reconnect_ms) >= self._reconnect_delay:
                self._last_reconnect_ms = now
                if self.connect():
                    self._reconnect_delay = _RECONNECT_BASE_MS
                else:
                    self._reconnect_delay = min(self._reconnect_delay * 2, _RECONNECT_MAX_MS)
            return

        try:
            self._read_frame()
        except OSError:
            print("[ws] connection lost — scheduling reconnect")
            self._connected = False
            self._close_socket()
        except Exception as e:
            print(f"[ws] poll error: {e}")

    def send_event(self, event_name, data=None):
        """Send a JSON event frame to the backend."""
        if not self._connected:
            print(f"[ws] send skipped (disconnected): {event_name}")
            return False
        payload = ujson.dumps({"event": event_name, "data": data or {}})
        try:
            frame = _build_frame(_OP_TEXT, payload.encode())
            self._sock.setblocking(True)
            self._sock.write(frame)
            self._sock.setblocking(False)
            return True
        except Exception as e:
            print(f"[ws] send error: {e}")
            self._connected = False
            self._close_socket()
            return False

    def is_connected(self):
        return self._connected

    # ── Internal ──────────────────────────────────────────────────────────────

    def _close_socket(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _read_frame(self):
        """
        Try to read one frame from socket (non-blocking).
        Raises OSError if socket closed.
        """
        if self._sock is None:
            raise OSError("no socket")

        # Peek at first byte non-blocking
        try:
            self._sock.setblocking(False)
            b0 = self._sock.read(1)
        except OSError:
            return  # EAGAIN — nothing available
        if not b0:
            raise OSError("socket EOF")

        self._sock.setblocking(True)
        b1 = _recv_exact(self._sock, 1)

        fin    = (b0[0] & 0x80) != 0
        opcode = b0[0] & 0x0F
        masked = (b1[0] & 0x80) != 0
        plen   = b1[0] & 0x7F

        if plen == 126:
            plen = struct.unpack(">H", _recv_exact(self._sock, 2))[0]
        elif plen == 127:
            plen = struct.unpack(">Q", _recv_exact(self._sock, 8))[0]

        mask_key = _recv_exact(self._sock, 4) if masked else None
        payload  = bytearray(_recv_exact(self._sock, plen))

        if masked and mask_key:
            for i in range(len(payload)):
                payload[i] ^= mask_key[i % 4]

        self._sock.setblocking(False)

        if opcode == _OP_PING:
            pong = _build_frame(_OP_PONG, bytes(payload))
            self._sock.setblocking(True)
            self._sock.write(pong)
            self._sock.setblocking(False)
            return

        if opcode == _OP_CLOSE:
            print("[ws] server sent CLOSE")
            raise OSError("server closed")

        if opcode in (_OP_TEXT, _OP_BINARY):
            try:
                msg = ujson.loads(bytes(payload))
                self._dispatch(msg)
            except ValueError as e:
                print(f"[ws] JSON parse error: {e}")

    def _dispatch(self, msg):
        event = msg.get("event") or msg.get("type")
        if not event:
            print(f"[ws] unknown message: {msg}")
            return
        handler = self._handlers.get(event)
        if handler:
            try:
                handler(msg.get("data", {}))
            except Exception as e:
                print(f"[ws] handler error for {event}: {e}")
        else:
            print(f"[ws] no handler for event: {event}")
