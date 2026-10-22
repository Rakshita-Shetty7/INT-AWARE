"""
Experimentation script to investigate and improve Leave-Families-Out Generalization.
Tests:
  1. Baseline (Raw TF-IDF + Calibrated LinearSVC)
  2. Enhanced Preprocessing (Noise stripping: pager pipes, echo, redirects, nohup)
  3. Enriched Tokenization (Subtoken parsing, path breakdown, flag extraction)
  4. Hybrid Domain Features (Target path types, shell primitives, redirect verbs)
  5. Classifier & Hyperparameter Exploration (Calibrated LinearSVC, LogisticRegression, MLP, Ensemble)
  6. Hybrid Rule-fallback Integration (as implemented in hybrid_classifier)
"""

import re
import sys
import collections
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report

from backend.app.ml.dataset import build_dataset
from backend.app.ml.split import stratified_group_split
from backend.app.ml.labels import INTENT_CLASSES

# 1. Clean command noise
def clean_cmd(cmd: str) -> str:
    c = cmd.strip()
    # Strip benign wrappers
    c = re.sub(r"\s*\|\s*(?:more|less|head(?:\s+-[n\d]+)?|tail(?:\s+-[n\d]+)?|tr\s+-[^\s]+(?:\s+[^\s]+)?)\s*$", "", c)
    c = re.sub(r"\s*(?:;|&&)\s*echo\s+\w+\s*$", "", c)
    c = re.sub(r"\s*(?:2>&1|2>/dev/null|>+/dev/null\s*2>&1)", "", c)
    c = re.sub(r"^\s*nohup\s+", "", c)
    c = re.sub(r"\s*&\s*$", "", c)
    return c.strip()

# 2. Structural & Domain Feature Extractor
SEMANTIC_PATTERNS = {
    # Cleanup patterns
    "hist_cleanup": re.compile(r"(HISTSIZE=0|HISTFILE=/dev/null|unset\s+HISTFILE|history\s+-c|ln\s+-[^\s]*s[^\s]*\s+/dev/null|shred\s+.*\.bash_history|rm\s+-[^\s]*\s+.*\.bash_history|journalctl\s+--vacuum)", re.I),
    "log_kill_cleanup": re.compile(r"((?:pkill|killall|systemctl\s+stop|service\s+\w+\s+stop)\s+.*(?:auditd|rsyslog|syslog|systemd-journald)|truncate\s+-[^\s]+\s+/var/log|rm\s+-[^\s]*\s+/var/log)", re.I),
    
    # Credential access patterns
    "ssh_key_read": re.compile(r"(cat|head|tail|less|more|grep|strings)\s+.*(?:\.ssh/id_|id_rsa|id_ecdsa|id_ed25519|authorized_keys|known_hosts)", re.I),
    "shadow_passwd_read": re.compile(r"(cat|head|tail|less|more|grep|awk|cut)\s+.*(?:/etc/shadow|/etc/gshadow|/etc/security/opasswd)", re.I),
    "cred_dump_tool": re.compile(r"(mimikatz|hashcat|john|hydra|medusa|pwdump|gsecdump|lazagne)", re.I),
    "ssh_dir_browse": re.compile(r"(ls|find|tree|dir)\s+.*(?:\.ssh|/etc/security)", re.I),
    
    # Privilege escalation patterns
    "sudoers_tamper": re.compile(r"(?:/etc/sudoers|/etc/sudoers\.d|NOPASSWD)", re.I),
    "passwd_write": re.compile(r"(?:>>\s*/etc/passwd|>>\s*/etc/shadow|useradd\s+-[^\s]*\s+-u\s+0|usermod\s+-[^\s]*a[^\s]*G\s+sudo)", re.I),
    "priv_binary": re.compile(r"(sudo\s|pkexec|doas|su\s+-|getcap|capsh|setfacl|chmod\s+[0-7]*[4-7][0-7]{3})", re.I),
    "kernel_compile_exploit": re.compile(r"(gcc\s+.*exploit|clang\s+.*exploit|pwnkit|dirtycow|overlayfs|baron_samedit)", re.I),
    
    # Exploitation patterns
    "vuln_scan_exploit": re.compile(r"(sqlmap|nikto|nmap\s+.*--script|msfconsole|msfvenom|cve-\d{4}-\d+|exploit-db|searchsploit)", re.I),
    
    # Persistence patterns
    "cron_tamper": re.compile(r"(crontab\s+-[^\s]*|/etc/cron|/var/spool/cron)", re.I),
    "service_tamper": re.compile(r"(/etc/systemd/system|/etc/init\.d|update-rc\.d|chkconfig|systemctl\s+enable)", re.I),
    "profile_tamper": re.compile(r"(/etc/profile|\.bashrc|\.profile|\.bash_login)", re.I),
    "ssh_key_append": re.compile(r"(>>\s*.*authorized_keys)", re.I),

    # Execution patterns
    "reverse_shell": re.compile(r"(/dev/tcp/|/dev/udp/|nc\s+-[^\s]*e|ncat\s+.*-e|mkfifo\s+.*\||bash\s+-i|python[23]?\s+-c\s+.*socket|perl\s+-e\s+.*Socket|ruby\s+-rsocket|php\s+-r\s+.*fsockopen)", re.I),
    "download_exec": re.compile(r"((?:curl|wget)\s+.*\|\s*(?:bash|sh|python|perl))", re.I),
    "chmod_exec": re.compile(r"(chmod\s+\+x\s+.*&&)", re.I),

    # Reconnaissance / Discovery
    "system_identity": re.compile(r"(uname\s|whoami|hostname|arch$|getconf\s+LONG_BIT|dpkg\s+--print-architecture|systemd-detect-virt|/etc/issue|/etc/os-release)", re.I),
    "env_recon": re.compile(r"(printenv|env$|export$|echo\s+\$[A-Za-z0-9_]+)", re.I),
    "network_enum": re.compile(r"(ifconfig|ip\s+a|netstat|ss\s|arp\s|route\s|cat\s+/proc/net|cat\s+/etc/networks)", re.I),
    "firewall_enum": re.compile(r"(ufw\s+status|iptables\s+-[LSN]|nft\s+list)", re.I),
    "file_discovery": re.compile(r"(find\s+/|locate\s|which\s|whereis\s|ls\s+-[^\s]*l|ls\s+/)", re.I),
    "user_enum": re.compile(r"(compgen\s+-u|getent\s+passwd|cat\s+/etc/passwd|users$|who$|w$)", re.I),
    "process_discovery": re.compile(r"(ps\s+aux|ps\s+-ef|top\s+-b|pstree)", re.I),

    # Benign / Other patterns
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
                row.append(1.0 if pat.search(cmd) else 0.0)
                
            # Additional structural cues:
            row.append(1.0 if ">>" in cmd else 0.0)
            row.append(1.0 if "|" in cmd else 0.0)
            row.append(1.0 if "&&" in cmd or ";" in cmd else 0.0)
            row.append(1.0 if ">" in cmd and ">>" not in cmd else 0.0)
            row.append(1.0 if "sudo" in cmd.lower() else 0.0)
            row.append(1.0 if "root" in cmd.lower() else 0.0)
            row.append(min(len(cmd) / 100.0, 3.0))
            features.append(row)
        return np.array(features, dtype=np.float32)

def command_token_extract(cmd: str) -> str:
    cleaned = clean_cmd(cmd)
    tokens = []
    # Primary binary and command prefix
    parts = cleaned.split()
    if parts:
        bin_name = re.sub(r"^.*/", "", parts[0]).lower()
        tokens.append(f"BIN__{bin_name}")
    
    # Path extraction and tokenization
    paths = re.findall(r"/[a-zA-Z0-9_\.\-]+(?:/[a-zA-Z0-9_\.\-]+)*", cleaned)
    for p in paths:
        tokens.append(f"PATH__{p.lower()}")
        for sub in p.split("/"):
            if sub:
                tokens.append(f"SUBPATH__{sub.lower()}")
                
    # Shell Flags
    flags = re.findall(r"--?[a-zA-Z0-9_\-]+", cleaned)
    for f in flags:
        tokens.append(f"FLAG__{f.lower()}")
        
    # Appends and redirects
    if ">>" in cleaned:
        tokens.append("OP__APPEND")
    if ">" in cleaned and ">>" not in cleaned:
        tokens.append("OP__REDIRECT")
    if "|" in cleaned:
        tokens.append("OP__PIPE")
    if "&&" in cleaned or ";" in cleaned:
        tokens.append("OP__CHAIN")
        
    return cleaned + " " + " ".join(tokens)

class TextCleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return [clean_cmd(cmd) for cmd in X]

class TokenEnricher(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return [command_token_extract(c) for c in X]



def run_experiment():
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
        
    print(f"Total commands: {len(commands)}, Train: {len(gX_tr)}, Test: {len(gX_te)}")
    
    # Experiment 1: Baseline
    base_features = FeatureUnion([
        ("word", TfidfVectorizer(token_pattern=r"(?u)\S+", ngram_range=(1, 3), min_df=1, sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 6), min_df=1, sublinear_tf=True, lowercase=True)),
    ])
    clf1 = CalibratedClassifierCV(LinearSVC(C=3.0, class_weight="balanced", max_iter=5000, random_state=1337), cv=5)
    pipe1 = Pipeline([("feats", base_features), ("clf", clf1)])
    pipe1.fit(gX_tr, gy_tr)
    pred1 = pipe1.predict(gX_te)
    print(f"Exp 1 (Baseline): Acc={accuracy_score(gy_te, pred1):.4f}, Macro-F1={f1_score(gy_te, pred1, average='macro'):.4f}")

    # Experiment 2: Cleaned text + TFIDF
    pipe2 = Pipeline([
        ("clean", TextCleaner()),
        ("feats", base_features),
        ("clf", clf1)
    ])
    pipe2.fit(gX_tr, gy_tr)
    pred2 = pipe2.predict(gX_te)
    print(f"Exp 2 (Cleaned TFIDF): Acc={accuracy_score(gy_te, pred2):.4f}, Macro-F1={f1_score(gy_te, pred2, average='macro'):.4f}")

    # Experiment 3: Cleaned text + Domain Features + TFIDF
    hybrid_features = FeatureUnion([
        ("word", Pipeline([("clean", TextCleaner()), ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\S+", ngram_range=(1, 3), min_df=1, sublinear_tf=True, lowercase=True))])),
        ("char", Pipeline([("clean", TextCleaner()), ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 6), min_df=1, sublinear_tf=True, lowercase=True))])),
        ("domain", DomainFeatureExtractor()),
    ])
    
    for c_val in [1.0, 3.0, 5.0, 10.0]:
        clf3 = CalibratedClassifierCV(LinearSVC(C=c_val, class_weight="balanced", max_iter=5000, random_state=1337), cv=5)
        pipe3 = Pipeline([("feats", hybrid_features), ("clf", clf3)])
        pipe3.fit(gX_tr, gy_tr)
        pred3 = pipe3.predict(gX_te)
        print(f"Exp 3 (Hybrid C={c_val}): Acc={accuracy_score(gy_te, pred3):.4f}, Macro-F1={f1_score(gy_te, pred3, average='macro'):.4f}")

    # Experiment 4: Logistic Regression on Hybrid Features
    for c_val in [1.0, 5.0, 10.0, 20.0]:
        clf4 = LogisticRegression(C=c_val, class_weight="balanced", max_iter=3000, random_state=1337)
        pipe4 = Pipeline([("feats", hybrid_features), ("clf", clf4)])
        pipe4.fit(gX_tr, gy_tr)
        pred4 = pipe4.predict(gX_te)
        print(f"Exp 4 (LogReg C={c_val}): Acc={accuracy_score(gy_te, pred4):.4f}, Macro-F1={f1_score(gy_te, pred4, average='macro'):.4f}")

    # Experiment 6: Token Enricher + Domain Features + TFIDF
    rich_features = FeatureUnion([
        ("word", Pipeline([("token_enrich", TokenEnricher()), ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\S+", ngram_range=(1, 3), min_df=1, sublinear_tf=True, lowercase=True))])),
        ("char", Pipeline([("token_enrich", TokenEnricher()), ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 6), min_df=1, sublinear_tf=True, lowercase=True))])),
        ("domain", DomainFeatureExtractor()),
    ])
    clf6 = CalibratedClassifierCV(LinearSVC(C=3.0, class_weight="balanced", max_iter=5000, random_state=1337), cv=5)
    pipe6 = Pipeline([("feats", rich_features), ("clf", clf6)])
    pipe6.fit(gX_tr, gy_tr)
    pred6 = pipe6.predict(gX_te)
    print(f"Exp 6 (TokenEnrich + Domain + LinearSVC): Acc={accuracy_score(gy_te, pred6):.4f}, Macro-F1={f1_score(gy_te, pred6, average='macro'):.4f}")

    # Experiment 7: Hybrid Rule Arbitration + ML
    # Evaluate hybrid decision: when strong semantic pattern fires with high specificity, arbitrate
    from datetime import datetime, timezone
    from backend.app.services.rule_classifier import RuleClassifier
    from backend.app.models.events import NormalizedEvent
    rule_engine = RuleClassifier()
    
    hybrid_preds = []
    rule_overrides = 0
    now = datetime.now(timezone.utc)
    for cmd, ml_p in zip(gX_te, pred6):
        evt = NormalizedEvent(event_id="eval", timestamp=now, session_id="eval", event_type="command", command=cmd)
        r_res = rule_engine.classify(evt)
        # If strong rule signature fired with >= 0.90 confidence and isn't OTHER:
        if r_res and r_res.rule_matches and r_res.confidence >= 0.90 and r_res.intent.value != "OTHER":
            hybrid_preds.append(r_res.intent.value)
            rule_overrides += 1
        else:
            hybrid_preds.append(ml_p)
            
    print(f"Exp 7 (Hybrid Rule Engine + Exp 6 ML): Acc={accuracy_score(gy_te, hybrid_preds):.4f}, Macro-F1={f1_score(gy_te, hybrid_preds, average='macro'):.4f} (Rule overrides: {rule_overrides})")


if __name__ == "__main__":
    run_experiment()
