"""
Canonical intent -> attack-stage mapping, shared by the ML classifier and any
consumer that needs a MITRE-aligned stage for a predicted intent.

Keeping this in one place guarantees the ML path emits the same AttackStage
values as the deterministic rule engine.
"""

from __future__ import annotations

# The 10 canonical intent classes, in a fixed order (used for reporting).
INTENT_CLASSES = [
    "RECONNAISSANCE",
    "DISCOVERY",
    "CREDENTIAL_ACCESS",
    "EXECUTION",
    "PRIVILEGE_ESCALATION",
    "PERSISTENCE",
    "EXPLOITATION",
    "EXFILTRATION",
    "CLEANUP",
    "OTHER",
]

# Intent -> AttackStage (string values match AttackStage enum members).
INTENT_TO_STAGE = {
    "RECONNAISSANCE": "RECONNAISSANCE",
    "DISCOVERY": "DISCOVERY",
    "CREDENTIAL_ACCESS": "CREDENTIAL_ACCESS",
    "EXECUTION": "EXECUTION",
    "PRIVILEGE_ESCALATION": "PRIVILEGE_ESCALATION",
    "PERSISTENCE": "PERSISTENCE",
    "EXPLOITATION": "EXECUTION",   # exploitation manifests during the execution stage
    "EXFILTRATION": "EXFILTRATION",
    "CLEANUP": "CLEANUP",
    "OTHER": "UNKNOWN",
}


def stage_for_intent(intent: str) -> str:
    """Returns the MITRE-aligned attack stage for a given intent (UNKNOWN if unmapped)."""
    return INTENT_TO_STAGE.get(intent, "UNKNOWN")
