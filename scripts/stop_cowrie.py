#!/usr/bin/env python3
"""
Cowrie Honeypot Stopper
Stops the running Cowrie process by reading var/run/cowrie.pid.
"""

import os
import signal
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HONEYPOT_DIR = PROJECT_ROOT / "honeypot"
PID_FILE = HONEYPOT_DIR / "var" / "run" / "cowrie.pid"

if not PID_FILE.exists():
    print("[!] Cowrie PID file not found. Cowrie may not be running.")
    sys.exit(0)

try:
    with open(PID_FILE, "r") as f:
        pid_str = f.read().strip()
        pid = int(pid_str)
except Exception as e:
    print(f"[-] Could not read PID file: {e}")
    sys.exit(1)

print(f"[*] Attempting to stop Cowrie process with PID: {pid}...")

try:
    if os.name == "nt":
        # Windows process termination
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True, capture_output=True)
    else:
        os.kill(pid, signal.SIGTERM)
    print(f"[+] Cowrie process (PID {pid}) stopped successfully.")
except Exception as e:
    print(f"[-] Failed to stop PID {pid}: {e}")

if PID_FILE.exists():
    try:
        PID_FILE.unlink()
    except Exception:
        pass
