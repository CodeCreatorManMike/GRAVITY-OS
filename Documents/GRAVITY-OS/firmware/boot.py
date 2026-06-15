# boot.py — MicroPython first-stage boot
# Runs before main.py. Keep this minimal.
# Enable REPL over USB CDC so you can interrupt with Ctrl-C during development.

import sys
import uos

# Ensure USB serial (CDC) REPL is available.
# On ESP32-S3 with native USB this is automatic when using the correct firmware build.
# Nothing else belongs here — all app logic lives in main.py.
