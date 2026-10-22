"""
Feature Extraction Utilities for ML Anomaly Detection and Risk Prediction.

Extracts dense numerical vectors from command strings and session contexts,
capturing structural, statistical, and security-relevant behavioral characteristics.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

# Sensitive system targets frequently accessed in cyber intrusions
SENSITIVE_TARGETS = [
    r"/etc/shadow", r"/etc/passwd", r"/etc/sudoers", r"/root", r"/proc/kcore",
    r"/dev/mem", r"/\.ssh", r"id_rsa", r"/etc/crontab", r"/var/log",
    r"/tmp/\.", r"/dev/shm", r"\.bash_history"
]
SENSITIVE_REGEX = re.compile("|".join(SENSITIVE_TARGETS), re.IGNORECASE)

# Dangerous/destructive command primitives
DESTRUCTIVE_PRIMITIVES = [
    r"\brm\s+-[rf]+", r"\bmkfs\b", r"\bdd\b", r"\bshred\b", r"\btruncate\b",
    r">\s*/dev/sd[a-z]", r">\s*/dev/null", r":\(\)\s*\{"
]
DESTRUCTIVE_REGEX = re.compile("|".join(DESTRUCTIVE_PRIMITIVES), re.IGNORECASE)

# Network exfiltration or payload download tools
NETWORK_PRIMITIVES = [
    r"\bcurl\b", r"\bwget\b", r"\bnc\b", r"\bnetcat\b", r"\btftp\b",
    r"\bscp\b", r"\brsync\b", r"\bsftp\b", r"\bssh\b", r"\btelnet\b"
]
NETWORK_REGEX = re.compile("|".join(NETWORK_PRIMITIVES), re.IGNORECASE)

# Privilege escalation triggers
PRIVESC_PRIMITIVES = [
    r"\bsudo\b", r"\bsu\b", r"\bpkexec\b", r"\bdoas\b", r"\bgetcap\b",
    r"\bcapsh\b", r"\bchmod\s+[0-7]*[4-7][0-7]{3}\b", r"\bchown\s+root\b"
]
PRIVESC_REGEX = re.compile("|".join(PRIVESC_PRIMITIVES), re.IGNORECASE)


# Out-of-Distribution & Critical Weaponization Attack Primitives
CRITICAL_ANOMALY_PATTERNS = [
    r"/dev/tcp", r"/dev/udp", r"mkfifo", r"reverse_tcp", r"shell_reverse",
    r"base64", r"\\x[0-9a-fA-F]{2}", r"pwnkit", r"dirtycow", r"looney_tunables",
    r"xmrig", r"miner", r"kdevtmpfsi", r"linpeas", r"chisel",
    r"\|\s*bash", r"\|\s*sh", r"python[23]?\s+-c", r"perl\s+-e", r"eval",
    r"pkexec", r"cve-\d{4}-\d+", r"shred", r"rm\s+-[rf]+\s+/"
]
CRITICAL_ANOMALY_REGEX = [re.compile(p, re.IGNORECASE) for p in CRITICAL_ANOMALY_PATTERNS]


def calculate_shannon_entropy(text: str) -> float:
    """Computes byte-level Shannon entropy of a string."""
    if not text:
        return 0.0
    freqs = {}
    for char in text:
        freqs[char] = freqs.get(char, 0) + 1
    entropy = 0.0
    length = len(text)
    for count in freqs.values():
        p = count / length
        entropy -= p * math.log2(p)
    return float(entropy)


def extract_command_features(cmd: str) -> np.ndarray:
    r"""
    Extracts a 30-dimensional clean dense numerical feature vector for command anomaly detection.
    Combines critical weaponization indicators, encoding patterns, Shannon entropy, and length.
    """
    cmd = cmd or ""
    length = len(cmd)
    if length == 0:
        return np.zeros(30, dtype=np.float32)

    hits = [1.0 if r.search(cmd) else 0.0 for r in CRITICAL_ANOMALY_REGEX]
    has_hex = 1.0 if (r"\x" in cmd or "%" in cmd) else 0.0
    has_base64 = 1.0 if re.search(r"[A-Za-z0-9+/]{20,}={0,2}", cmd) else 0.0
    entropy = calculate_shannon_entropy(cmd)

    prefix_feats = [
        sum(hits),
        has_hex,
        has_base64,
        1.0 if (any(hits) or has_hex > 0 or has_base64 > 0) else 0.0,
        min(entropy / 8.0, 1.0),
        min(length / 200.0, 1.0),
    ]

    return np.array(prefix_feats + hits, dtype=np.float32)


def extract_risk_features(
    cmd: str,
    intent_onehot: Optional[np.ndarray] = None,
    session_command_count: int = 1,
    failed_logins: int = 0,
    session_duration_s: float = 0.0
) -> np.ndarray:
    """
    Extracts a dense feature vector for Gradient Boosting risk score regression.
    Combines 16 command structural features + 10 intent one-hot values + 4 session context features.
    Total: 30 dimensions.
    """
    cmd_feats = extract_command_features(cmd)
    if intent_onehot is None or len(intent_onehot) != 10:
        intent_feats = np.zeros(10, dtype=np.float32)
    else:
        intent_feats = np.array(intent_onehot, dtype=np.float32)

    session_feats = np.array([
        min(session_command_count / 50.0, 1.0),
        min(failed_logins / 10.0, 1.0),
        min(session_duration_s / 600.0, 1.0),
        1.0 if failed_logins > 0 else 0.0,
    ], dtype=np.float32)

    return np.concatenate([cmd_feats, intent_feats, session_feats])


# --------------------------------------------------------------------------- #
# Enhanced Domain Feature Extraction for Generalization to Novel Command Families
# --------------------------------------------------------------------------- #

def clean_cmd(cmd: str) -> str:
    """Canonicalize command by stripping noise wrappers (pagers, redirects, nohup)."""
    c = (cmd or "").strip()
    c = re.sub(r"\s*\|\s*(?:more|less|head(?:\s+-[n\d]+)?|tail(?:\s+-[n\d]+)?|tr\s+-[^\s]+(?:\s+[^\s]+)?)\s*$", "", c)
    c = re.sub(r"\s*(?:;|&&)\s*echo\s+\w+\s*$", "", c)
    c = re.sub(r"\s*(?:2>&1|2>/dev/null|>+/dev/null\s*2>&1)", "", c)
    c = re.sub(r"^\s*nohup\s+", "", c)
    c = re.sub(r"\s*&\s*$", "", c)
    return c.strip()


SEMANTIC_INTENT_PATTERNS = {
    # Cleanup & Defense Evasion
    "hist_cleanup": re.compile(r"(HISTSIZE=0|HISTFILE=/dev/null|unset\s+HISTFILE|history\s+-c|ln\s+-[^\s]*s[^\s]*\s+/dev/null|shred\s+.*\.bash_history|rm\s+-[^\s]*\s+.*\.bash_history|journalctl\s+--vacuum)", re.I),
    "log_kill_cleanup": re.compile(r"((?:pkill|killall|systemctl\s+stop|service\s+\w+\s+stop)\s+.*(?:auditd|rsyslog|syslog|systemd-journald)|truncate\s+-[^\s]+\s+/var/log|rm\s+-[^\s]*\s+/var/log)", re.I),
    
    # Credential Access
    "ssh_key_read": re.compile(r"(cat|head|tail|less|more|grep|strings)\s+.*(?:\.ssh/id_|id_rsa|id_ecdsa|id_ed25519|authorized_keys|known_hosts)", re.I),
    "shadow_passwd_read": re.compile(r"(cat|head|tail|less|more|grep|awk|cut)\s+.*(?:/etc/shadow|/etc/gshadow|/etc/security/opasswd)", re.I),
    "cred_dump_tool": re.compile(r"(mimikatz|hashcat|john|hydra|medusa|pwdump|gsecdump|lazagne)", re.I),
    "ssh_dir_browse": re.compile(r"(?:ls|find|tree|dir)\s+.*(?:\.ssh)", re.I),
    
    # Privilege Escalation
    "sudoers_tamper": re.compile(r"(?:/etc/sudoers|/etc/sudoers\.d|NOPASSWD)", re.I),
    "passwd_write": re.compile(r"(?:>>\s*/etc/passwd|>>\s*/etc/shadow|useradd\s+-[^\s]*\s+-u\s+0|usermod\s+-[^\s]*a[^\s]*G\s+sudo)", re.I),
    "priv_binary": re.compile(r"(sudo\s|pkexec|doas|su\s+-|getcap|capsh|setfacl|chmod\s+[0-7]*[4-7][0-7]{3})", re.I),
    "kernel_compile_exploit": re.compile(r"(gcc\s+.*exploit|clang\s+.*exploit|pwnkit|dirtycow|overlayfs|baron_samedit)", re.I),
    
    # Exploitation
    "vuln_scan_exploit": re.compile(r"(sqlmap|nikto|nmap\s+.*--script|msfconsole|msfvenom|cve-\d{4}-\d+|exploit-db|searchsploit)", re.I),
    
    # Persistence
    "cron_tamper": re.compile(r"(crontab\s+-[^\s]*|/etc/cron|/var/spool/cron)", re.I),
    "service_tamper": re.compile(r"(/etc/systemd/system|/etc/init\.d|update-rc\.d|chkconfig|systemctl\s+enable)", re.I),
    "profile_tamper": re.compile(r"(/etc/profile|\.bashrc|\.profile|\.bash_login)", re.I),
    "ssh_key_append": re.compile(r"(>>\s*.*authorized_keys)", re.I),

    # Execution
    "reverse_shell": re.compile(r"(/dev/tcp/|/dev/udp/|nc\s+-[^\s]*e|ncat\s+.*-e|mkfifo\s+.*\||bash\s+-i|python[23]?\s+-c\s+.*socket|perl\s+-e\s+.*Socket|ruby\s+-rsocket|php\s+-r\s+.*fsockopen)", re.I),
    "download_exec": re.compile(r"((?:curl|wget)\s+.*\|\s*(?:bash|sh|python|perl))", re.I),
    "chmod_exec": re.compile(r"(chmod\s+\+x\s+.*&&)", re.I),

    # Reconnaissance / Discovery
    "system_identity": re.compile(r"(uname\s|whoami|hostname|arch$|getconf\s+LONG_BIT|dpkg\s+--print-architecture|systemd-detect-virt|/etc/issue|/etc/os-release)", re.I),
    "env_recon": re.compile(r"(printenv|env$|export$|echo\s+\$[A-Za-z0-9_]+)", re.I),
    "network_enum": re.compile(r"(ifconfig|ip\s+a|netstat|ss\s|arp\s|route\s|cat\s+/proc/net|cat\s+/etc/networks)", re.I),
    "firewall_enum": re.compile(r"(ufw\s+status|iptables\s+-[LSN]|nft\s+list)", re.I),
    "file_discovery": re.compile(r"(find\s+/|locate\s|which\s|whereis\s|ls\s+-[^\s]*l|ls\s+/(?!home/.*\.ssh))", re.I),
    "user_enum": re.compile(r"(compgen\s+-u|getent\s+passwd|cat\s+/etc/passwd|users$|who$|w$)", re.I),
    "process_discovery": re.compile(r"(ps\s+aux|ps\s+-ef|top\s+-b|pstree)", re.I),

    # Benign / Other
    "other_help": re.compile(r"(--help\b|-h\b|man\s+\w+|info\s+\w+|help\s+\w+)", re.I),
    "other_pkg_mgr": re.compile(r"(apt\s+(?:list|search|update)|yum\s+(?:list|update)|dnf\s+|pacman\s+-[Ssy])", re.I),
    "other_time_date": re.compile(r"(timedatectl|date\b|uptime\b|cal\b)", re.I),

    # Exfiltration
    "archive_exfil": re.compile(r"(tar\s+.*\|\s*(?:curl|nc|wget)|base64\s+.*\|\s*(?:curl|nc)|scp\s+|rsync\s+.*@|curl\s+-[^\s]*F\s+file=@)", re.I),
}


class TextCleaner(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible transformer that cleans command strings."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return [clean_cmd(cmd) for cmd in X]


class DomainFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Extracts dense structural and semantic features from commands to improve
    generalization across unseen command templates and families.
    """
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for raw in X:
            cmd = clean_cmd(raw)
            row = []
            for _, pat in SEMANTIC_INTENT_PATTERNS.items():
                row.append(3.0 if pat.search(cmd) else 0.0)
            row.append(1.0 if ">>" in cmd else 0.0)
            row.append(1.0 if "|" in cmd else 0.0)
            row.append(1.0 if "&&" in cmd or ";" in cmd else 0.0)
            row.append(1.0 if ">" in cmd and ">>" not in cmd else 0.0)
            row.append(1.0 if "sudo" in cmd.lower() else 0.0)
            row.append(1.0 if "root" in cmd.lower() else 0.0)
            row.append(min(len(cmd) / 100.0, 3.0))
            features.append(row)
        return np.array(features, dtype=np.float32)

