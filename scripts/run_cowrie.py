#!/usr/bin/env python3
"""
Cowrie Honeypot Runner
Starts the Cowrie service cleanly using Twisted within the project's isolated honeypot environment.
"""

import os
import sys
from pathlib import Path

# Ensure honeypot root is working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
HONEYPOT_DIR = PROJECT_ROOT / "honeypot"

if not HONEYPOT_DIR.exists():
    print(f"Error: Honeypot directory not found at {HONEYPOT_DIR}")
    sys.exit(1)

os.chdir(HONEYPOT_DIR)

# Verify cowrie configuration exists
config_path = HONEYPOT_DIR / "etc" / "cowrie.cfg"
if not config_path.exists():
    print(f"Error: Configuration file not found at {config_path}")
    sys.exit(1)

# Ensure var directories exist
(HONEYPOT_DIR / "var" / "run").mkdir(parents=True, exist_ok=True)
(HONEYPOT_DIR / "var" / "log" / "cowrie").mkdir(parents=True, exist_ok=True)
(HONEYPOT_DIR / "var" / "lib" / "cowrie").mkdir(parents=True, exist_ok=True)

pid_file = HONEYPOT_DIR / "var" / "run" / "cowrie.pid"

# Write PID
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))

print(f"[*] Starting Cowrie Honeypot on 127.0.0.1:2222 (PID: {os.getpid()})...")
print(f"[*] State Directory: {HONEYPOT_DIR}")
print(f"[*] JSON Log: {HONEYPOT_DIR / 'var' / 'log' / 'cowrie' / 'cowrie.json'}")

try:
    from twisted.plugins.cowrie_plugin import serviceMaker
    from twisted.internet import reactor

    options = serviceMaker.options()
    service = serviceMaker.makeService(options)
    service.startService()

    def clean_shutdown():
        print("\n[*] Stopping Cowrie service...")
        if service.running:
            service.stopService()
        if pid_file.exists():
            try:
                pid_file.unlink()
            except Exception:
                pass
        print("[*] Cowrie stopped.")

    reactor.addSystemEventTrigger("before", "shutdown", clean_shutdown)
    print("[+] Cowrie is running and listening for connections.")
    reactor.run()

except KeyboardInterrupt:
    pass
except Exception as e:
    print(f"[-] Error running Cowrie: {e}")
finally:
    if pid_file.exists():
        try:
            pid_file.unlink()
        except Exception:
            pass
