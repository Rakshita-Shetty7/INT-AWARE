#!/usr/bin/env python3
"""
Controlled Honeypot Test Client
Performs safe, harmless, controlled interactions against the local Cowrie instance to generate telemetry.
"""

import sys
import time
import paramiko

def run_controlled_test(host="127.0.0.1", port=2222, username="root", password="password"):
    print(f"[*] Connecting to honeypot at {host}:{port} with user '{username}'...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        print("[+] SSH connection authenticated successfully!")
        
        commands = [
            "whoami",
            "uname -a",
            "id",
            "ls -la /",
            "cat /etc/issue",
            "exit"
        ]
        
        # Open interactive shell session
        channel = client.invoke_shell()
        time.sleep(1)
        
        for cmd in commands:
            print(f"[*] Executing test command: {cmd}")
            channel.send(cmd + "\n")
            time.sleep(1)
            
            # Read output if any
            if channel.recv_ready():
                output = channel.recv(4096).decode("utf-8", errors="ignore")
                for line in output.splitlines():
                    if line.strip():
                        print(f"    > {line}")

        channel.close()
        client.close()
        print("[+] Controlled test session completed successfully.")
        return True
        
    except Exception as e:
        print(f"[-] Controlled test failed: {e}")
        return False

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 2222
    user = sys.argv[3] if len(sys.argv) > 3 else "root"
    pwd = sys.argv[4] if len(sys.argv) > 4 else "root"
    
    run_controlled_test(host=host, port=port, username=user, password=pwd)
