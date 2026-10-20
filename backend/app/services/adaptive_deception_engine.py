"""
Safe Adaptive Deception Engine.

Selects and synthesizes approved simulated honeypot responses, dynamic decoy
artifacts, and honeytokens conditioned on observed attacker intent and session context.

SAFETY GUARANTEE:
  * ZERO HOST EXECUTION: Attacker commands are NEVER passed to the underlying
    operating system shell (no subprocess, no os.system, no popen).
  * All responses are generated through bounded templates, synthetic honeytokens,
    or sandboxed virtual filesystem representations.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.intent import AttackStage, IntentCategory

logger = logging.getLogger(__name__)


class DeceptionStrategy(str, Enum):
    """Categorical deception intervention strategies."""
    SIMULATED_SUCCESS = "SIMULATED_SUCCESS"
    HONEYTOKEN_INJECTION = "HONEYTOKEN_INJECTION"
    DECOY_ARTIFACT = "DECOY_ARTIFACT"
    TARPIT_DELAY = "TARPIT_DELAY"
    DECOY_ERROR = "DECOY_ERROR"
    DEFLECTION = "DEFLECTION"


class DeceptionDecision(BaseModel):
    """Auditable log record of a generated deception response."""
    decision_id: str = Field(..., description="Unique deterministic decision ID")
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trigger_command: Optional[str] = None
    trigger_intent: IntentCategory
    current_stage: AttackStage
    strategy: DeceptionStrategy
    policy_id: str
    delay_ms: int = Field(0, description="Emulated processing latency for tar-pitting")
    decoy_payload: str = Field(..., description="Synthetic output returned to honeypot shell")
    honeytokens_injected: List[str] = Field(default_factory=list, description="Canary tokens embedded in response")
    rationale: str


class AdaptiveDeceptionEngine:
    """
    State-aware cyber deception controller.
    Dynamically generates deceptive telemetry while enforcing strict zero-host isolation.
    """

    def __init__(self, canary_prefix: str = "CANARY_INTAWARE"):
        self.canary_prefix = canary_prefix

    def _generate_canary_token(self, session_id: str, token_type: str) -> str:
        """Generates a deterministic yet unique trackable canary honeytoken."""
        seed = f"{session_id}:{token_type}:canary_salt"
        digest = hashlib.sha256(seed.encode()).hexdigest()[:16]
        return f"{self.canary_prefix}_{token_type.upper()}_{digest}"

    def select_deception_response(
        self,
        command: Optional[str],
        intent: IntentCategory,
        attack_stage: AttackStage,
        session_id: str,
        risk_score: int = 0,
    ) -> DeceptionDecision:
        """
        Synthesizes an intent-conditioned deception response with zero host execution.
        """
        cmd_clean = (command or "").strip()
        cmd_lower = cmd_clean.lower()
        now = datetime.now(timezone.utc)
        decision_id = f"dec_{hashlib.md5(f'{session_id}:{cmd_clean}:{now.isoformat()}'.encode()).hexdigest()[:12]}"

        # ------------------------------------------------------------------ #
        # 1. Reconnaissance / System Fingerprinting
        # ------------------------------------------------------------------ #
        if intent == IntentCategory.RECONNAISSANCE or any(k in cmd_lower for k in ["uname", "whoami", "id", "hostname", "ifconfig", "ip a"]):
            if "uname" in cmd_lower:
                payload = "Linux debian-target-prod 5.10.0-8-amd64 #1 SMP Debian 5.10.46-4 x86_64 GNU/Linux\n"
            elif "whoami" in cmd_lower:
                payload = "root\n"
            elif "id" in cmd_lower:
                payload = "uid=0(root) gid=0(root) groups=0(root)\n"
            elif "hostname" in cmd_lower:
                payload = "prod-db-internal-01\n"
            elif "ifconfig" in cmd_lower or "ip a" in cmd_lower:
                payload = (
                    "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
                    "        inet 10.100.4.15  netmask 255.255.255.0  broadcast 10.100.4.255\n"
                    "        inet6 fe80::a00:27ff:fe4e:66a1  prefixlen 64  scopeid 0x20<link>\n"
                    "        ether 08:00:27:4e:66:a1  txqueuelen 1000  (Ethernet)\n"
                )
            else:
                payload = "Linux workstation 5.15.0-generic\n"

            return DeceptionDecision(
                decision_id=decision_id,
                session_id=session_id,
                trigger_command=cmd_clean,
                trigger_intent=intent,
                current_stage=attack_stage,
                strategy=DeceptionStrategy.SIMULATED_SUCCESS,
                policy_id="POL_RECON_EMULATION",
                delay_ms=25,
                decoy_payload=payload,
                honeytokens_injected=[],
                rationale="Returned plausible host profile to encourage continued non-destructive interaction.",
            )

        # ------------------------------------------------------------------ #
        # 2. Credential Access / Shadow / Secrets Hunting
        # ------------------------------------------------------------------ #
        if intent == IntentCategory.CREDENTIAL_ACCESS or any(k in cmd_lower for k in ["shadow", "passwd", "id_rsa", "aws", "token", "env"]):
            canary_key = self._generate_canary_token(session_id, "API_KEY")
            canary_pass = self._generate_canary_token(session_id, "PASS")

            if "shadow" in cmd_lower:
                payload = (
                    f"root:$6$rounds=5000$saltsalt$CANARY_HASH_{canary_pass[:8]}:18890:0:99999:7:::\n"
                    "daemon:*:18890:0:99999:7:::\n"
                    f"admin:$6$rounds=5000$saltsalt$CANARY_HASH_{canary_pass[8:]}:18890:0:99999:7:::\n"
                )
            elif "id_rsa" in cmd_lower:
                payload = (
                    "-----BEGIN OPENSSH PRIVATE KEY-----\n"
                    f"b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn\n"
                    f"NhAAAA{canary_key}FakeKeyPaddingDataForHoneypotAttraction==\n"
                    "-----END OPENSSH PRIVATE KEY-----\n"
                )
            elif "aws" in cmd_lower or "env" in cmd_lower:
                payload = (
                    f"AWS_ACCESS_KEY_ID={canary_key}\n"
                    f"AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCY{canary_pass[:12]}\n"
                    "AWS_DEFAULT_REGION=us-east-1\n"
                )
            else:
                payload = (
                    "root:x:0:0:root:/root:/bin/bash\n"
                    "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                    "admin:x:1000:1000:Administrator:/home/admin:/bin/bash\n"
                )

            return DeceptionDecision(
                decision_id=decision_id,
                session_id=session_id,
                trigger_command=cmd_clean,
                trigger_intent=intent,
                current_stage=attack_stage,
                strategy=DeceptionStrategy.HONEYTOKEN_INJECTION,
                policy_id="POL_HONEYTOKEN_CRED_INJECTION",
                delay_ms=45,
                decoy_payload=payload,
                honeytokens_injected=[canary_key, canary_pass],
                rationale="Injected synthetic honeytoken credential to detect out-of-band credential usage.",
            )

        # ------------------------------------------------------------------ #
        # 3. Discovery / File System Enumeration
        # ------------------------------------------------------------------ #
        if intent == IntentCategory.DISCOVERY or any(k in cmd_lower for k in ["ls", "find", "cat", "ps", "netstat", "lsof"]):
            canary_doc = self._generate_canary_token(session_id, "DOC")
            if "ls" in cmd_lower:
                payload = (
                    "total 36\n"
                    "drwxr-xr-x 4 root root 4096 Oct 12 10:20 .\n"
                    "drwxr-xr-x 8 root root 4096 Oct 10 09:15 ..\n"
                    f"-rw-r--r-- 1 root root  420 Oct 12 10:22 backup_credentials_{canary_doc[:6]}.txt\n"
                    "-rw-r--r-- 1 root root 1204 Oct 11 18:30 database_dump.sql\n"
                    "drwxr-xr-x 2 root root 4096 Oct 10 12:00 logs\n"
                )
            elif "ps" in cmd_lower:
                payload = (
                    "PID TTY          TIME CMD\n"
                    "  1 ?        00:00:02 systemd\n"
                    "142 ?        00:00:00 sshd\n"
                    "412 ?        00:00:01 mysqld\n"
                    "890 ?        00:00:00 apache2\n"
                )
            else:
                payload = f"# Configuration file\nDB_HOST=127.0.0.1\nDB_USER=appuser\nCANARY_REF={canary_doc}\n"

            return DeceptionDecision(
                decision_id=decision_id,
                session_id=session_id,
                trigger_command=cmd_clean,
                trigger_intent=intent,
                current_stage=attack_stage,
                strategy=DeceptionStrategy.DECOY_ARTIFACT,
                policy_id="POL_DECOY_DISCOVERY",
                delay_ms=30,
                decoy_payload=payload,
                honeytokens_injected=[canary_doc],
                rationale="Returned synthetic decoy file listings containing tempting canary artifacts.",
            )

        # ------------------------------------------------------------------ #
        # 4. Execution / Exploitation / Malware Staging (Tar-pitting Delay)
        # ------------------------------------------------------------------ #
        if intent in [IntentCategory.EXECUTION, IntentCategory.EXPLOITATION, IntentCategory.PRIVILEGE_ESCALATION]:
            # Apply intentional tar-pit delay (200ms - 800ms) to exhaust automated scanner cadence
            delay = min(800, max(200, 150 + (risk_score * 5)))
            payload = "Operation completed with status 0\n"

            return DeceptionDecision(
                decision_id=decision_id,
                session_id=session_id,
                trigger_command=cmd_clean,
                trigger_intent=intent,
                current_stage=attack_stage,
                strategy=DeceptionStrategy.TARPIT_DELAY,
                policy_id="POL_TARPIT_THROTTLE",
                delay_ms=delay,
                decoy_payload=payload,
                honeytokens_injected=[],
                rationale=f"Throttled execution with {delay}ms delay to exhaust scanner bandwidth and log payload.",
            )

        # ------------------------------------------------------------------ #
        # 5. Default Fallback Policy
        # ------------------------------------------------------------------ #
        return DeceptionDecision(
            decision_id=decision_id,
            session_id=session_id,
            trigger_command=cmd_clean,
            trigger_intent=intent,
            current_stage=attack_stage,
            strategy=DeceptionStrategy.SIMULATED_SUCCESS,
            policy_id="POL_DEFAULT_SANDBOX",
            delay_ms=10,
            decoy_payload="\n",
            honeytokens_injected=[],
            rationale="Default isolated sandbox acknowledgement.",
        )


# Global singleton
adaptive_deception_engine = AdaptiveDeceptionEngine()
