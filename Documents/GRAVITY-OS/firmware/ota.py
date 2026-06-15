# ota.py — OTA firmware update
#
# Flow:
#   1. Backend sends FIRMWARE_UPDATE_AVAILABLE event with {"version": "x.y.z", "url": "..."}
#   2. check_and_apply() compares versions; if newer, downloads .py files and writes them.
#   3. After all files written, triggers machine.reset().
#
# For V1 the backend will not push OTA in production, but the infrastructure is here.
# Only log to console if a newer version is available (per spec for initial build).

import urequests
import ujson
import uos
import machine
import config

_TEMP_DIR = "/ota_tmp"


def _version_tuple(s):
    """Convert "1.2.3" → (1, 2, 3)."""
    try:
        return tuple(int(x) for x in s.split("."))
    except Exception:
        return (0, 0, 0)


def check_and_apply(event_data):
    """
    Handle FIRMWARE_UPDATE_AVAILABLE event data.
    event_data = {"version": "0.2.0", "url": "http://host/firmware.json", "manifest": [...]}
    """
    remote_ver = event_data.get("version", "0.0.0")
    current_ver = config.FIRMWARE_VERSION

    if _version_tuple(remote_ver) <= _version_tuple(current_ver):
        print(f"[ota] firmware up to date ({current_ver})")
        return False

    print(f"[ota] new firmware available: {remote_ver} (current: {current_ver})")
    print("[ota] OTA update triggered — downloading ...")

    url = event_data.get("url")
    if not url:
        print("[ota] no URL in event — skipping")
        return False

    try:
        _download_and_apply(url, remote_ver)
        return True
    except Exception as e:
        print(f"[ota] update failed: {e}")
        _cleanup_temp()
        return False


def _download_and_apply(manifest_url, new_version):
    """
    Download manifest JSON, then each file listed, write to flash, reset.
    Manifest format:
      {"version": "0.2.0", "files": [{"path": "main.py", "url": "http://..."}, ...]}
    """
    import urequests

    print(f"[ota] fetching manifest: {manifest_url}")
    resp = urequests.get(manifest_url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"manifest HTTP {resp.status_code}")
    manifest = ujson.loads(resp.text)
    resp.close()

    files = manifest.get("files", [])
    if not files:
        print("[ota] manifest has no files")
        return

    # Create temp dir
    try:
        uos.mkdir(_TEMP_DIR)
    except OSError:
        pass

    downloaded = []
    for entry in files:
        path = entry["path"]
        url  = entry["url"]
        tmp  = _TEMP_DIR + "/" + path.replace("/", "_")
        print(f"[ota] downloading {path} ...")
        _download_file(url, tmp)
        downloaded.append((tmp, path))

    # All downloaded — now move into place
    print("[ota] applying update ...")
    for tmp, dest in downloaded:
        # Ensure destination directory exists
        parts = dest.rsplit("/", 1)
        if len(parts) > 1 and parts[0]:
            _makedirs(parts[0])
        _replace(tmp, "/" + dest)

    # Update version in config (write a new config.py with updated version)
    _bump_version(new_version)

    _cleanup_temp()
    print(f"[ota] update complete — rebooting to {new_version}")
    machine.reset()


def _download_file(url, dest_path):
    import urequests
    resp = urequests.get(url, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} for {url}")
    with open(dest_path, "w") as f:
        f.write(resp.text)
    resp.close()


def _replace(src, dst):
    try:
        uos.remove(dst)
    except OSError:
        pass
    uos.rename(src, dst)


def _makedirs(path):
    parts = path.strip("/").split("/")
    current = ""
    for part in parts:
        current += "/" + part
        try:
            uos.mkdir(current)
        except OSError:
            pass


def _cleanup_temp():
    try:
        for name in uos.listdir(_TEMP_DIR):
            uos.remove(_TEMP_DIR + "/" + name)
        uos.rmdir(_TEMP_DIR)
    except Exception:
        pass


def _bump_version(new_version):
    """Rewrite config.py with the updated FIRMWARE_VERSION."""
    try:
        with open("/config.py", "r") as f:
            src = f.read()
        old_line = f'FIRMWARE_VERSION = "{config.FIRMWARE_VERSION}"'
        new_line = f'FIRMWARE_VERSION = "{new_version}"'
        src = src.replace(old_line, new_line)
        with open("/config.py", "w") as f:
            f.write(src)
        print(f"[ota] config.py version updated to {new_version}")
    except Exception as e:
        print(f"[ota] version bump failed: {e}")
