import sys
import re
from pathlib import Path
from datetime import datetime, timezone
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

sys.path.insert(0, str(Path.cwd()))
from backend.app.ml.dataset import build_dataset
from backend.app.ml.split import stratified_group_split
from backend.app.ml.labels import INTENT_CLASSES

def clean_cmd(cmd: str) -> str:
    c = cmd.strip()
    c = re.sub(r"\s*\|\s*(?:more|less|head(?:\s+-[n\d]+)?|tail(?:\s+-[n\d]+)?|tr\s+-[^\s]+(?:\s+[^\s]+)?)\s*$", "", c)
    c = re.sub(r"\s*(?:;|&&)\s*echo\s+\w+\s*$", "", c)
    c = re.sub(r"\s*(?:2>&1|2>/dev/null|>+/dev/null\s*2>&1)", "", c)
    c = re.sub(r"^\s*nohup\s+", "", c)
    c = re.sub(r"\s*&\s*$", "", c)
    return c.strip()

SEMANTIC_PATTERNS = {
    # Cleanup
    "hist_cleanup": re.compile(r"(HISTSIZE=0|HISTFILE=/dev/null|unset\s+HISTFILE|history\s+-c|ln\s+-[^\s]*s[^\s]*\s+/dev/null|shred\s+.*\.bash_history|rm\s+-[^\s]*\s+.*\.bash_history|journalctl\s+--vacuum)", re.I),
    "log_kill_cleanup": re.compile(r"((?:pkill|killall|systemctl\s+stop|service\s+\w+\s+stop)\s+.*(?:auditd|rsyslog|syslog|systemd-journald)|truncate\s+-[^\s]+\s+/var/log|rm\s+-[^\s]*\s+/var/log)", re.I),
    
    # Credential access
    "ssh_key_read": re.compile(r"(cat|head|tail|less|more|grep|strings)\s+.*(?:\.ssh/id_|id_rsa|id_ecdsa|id_ed25519|authorized_keys|known_hosts)", re.I),
    "shadow_passwd_read": re.compile(r"(cat|head|tail|less|more|grep|awk|cut)\s+.*(?:/etc/shadow|/etc/gshadow|/etc/security/opasswd)", re.I),
    "cred_dump_tool": re.compile(r"(mimikatz|hashcat|john|hydra|medusa|pwdump|gsecdump|lazagne)", re.I),
    "ssh_dir_browse": re.compile(r"(?:ls|find|tree|dir)\s+.*(?:\.ssh)", re.I),
    
    # Privilege escalation
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

class DomainFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        features = []
        for raw in X:
            cmd = clean_cmd(raw)
            row = []
            for name, pat in SEMANTIC_PATTERNS.items():
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

class TextCleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return [clean_cmd(cmd) for cmd in X]

def main():
    raw_cmds, raw_labs, raw_grps = build_dataset()
    seen = set()
    commands, labels, groups = [], [], []
    for c, l, g in zip(raw_cmds, raw_labs, raw_grps):
        if c not in seen:
            seen.add(c)
            commands.append(c)
            labels.append(l)
            groups.append(g)

    gX_tr, gy_tr, gg_tr, gX_te, gy_te, gg_te = stratified_group_split(
        commands, labels, groups, test_size=0.2, seed=1337)

    features = FeatureUnion([
        ("word", Pipeline([("clean", TextCleaner()), ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\S+", ngram_range=(1, 3), min_df=1, sublinear_tf=True, lowercase=True))])),
        ("char", Pipeline([("clean", TextCleaner()), ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 6), min_df=1, sublinear_tf=True, lowercase=True))])),
        ("domain", DomainFeatureExtractor()),
    ])

    clf = CalibratedClassifierCV(LinearSVC(C=3.0, class_weight="balanced", max_iter=5000, random_state=1337), cv=5)
    pipe = Pipeline([("feats", features), ("clf", clf)])
    pipe.fit(gX_tr, gy_tr)
    preds = pipe.predict(gX_te)
    
    acc = accuracy_score(gy_te, preds)
    f1 = f1_score(gy_te, preds, average="macro")
    print(f"Results on Leave-Families-Out:")
    print(f"Accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(f"Macro-F1 : {f1:.4f}")
    print("\nDetailed Report:")
    print(classification_report(gy_te, preds, digits=4))

if __name__ == "__main__":
    main()
