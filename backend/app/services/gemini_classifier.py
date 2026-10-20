"""
Google Gemini Intent Classifier Service.
Uses the official google-genai SDK to analyze sanitized behavioral telemetry with structured schema enforcement.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from backend.app.config import settings
from backend.app.config import is_gemini_api_key_configured
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import (
    AttackStage,
    GeminiClassification,
    IntentCategory,
)

logger = logging.getLogger(__name__)

# System instructions guiding Gemini cybersecurity intent analysis
SYSTEM_INSTRUCTION = """
You are an expert cybersecurity intent analysis system operating inside an Intent-Aware Deception System (Honeypot).
Your task is to analyze observed honeypot attacker telemetry and classify the attacker's primary intent and MITRE ATT&CK stage.

You must choose strictly from the allowed taxonomies:
Intent Categories:
- RECONNAISSANCE: Querying system host, user identity, OS, hardware, or uptime.
- DISCOVERY: Exploring files, directories, processes, open ports, network interfaces, or configurations.
- CREDENTIAL_ACCESS: Brute forcing passwords, dumping shadow files, searching for private keys or bash history.
- EXECUTION: Dropping payloads, executing remote scripts, inline scripting, or reverse shells.
- PRIVILEGE_ESCALATION: Attempting sudo switching, abusing SUID binaries, or escalating to root.
- PERSISTENCE: Configuring crontabs, adding SSH keys, creating accounts, or modifying startup services.
- EXPLOITATION: Firing known vulnerability probes (e.g. Shellshock) or memory/command injection exploits.
- EXFILTRATION: Archiving or transmitting data offsite (e.g. scp, curl POST with files).
- CLEANUP: Erasing shell history, wiping logs, or unsetting audit trails.
- OTHER: Benign navigation (cd, pwd, clear) or unclassified connection handshakes.

Attack Stages:
- INITIAL_ACCESS, RECONNAISSANCE, DISCOVERY, EXECUTION, CREDENTIAL_ACCESS, PRIVILEGE_ESCALATION, PERSISTENCE, EXFILTRATION, CLEANUP, UNKNOWN.

Rules:
1. Base your classification strictly on the observed command and session context.
2. Provide a calibrated confidence score between 0.0 and 1.0.
3. Be concise and precise in your reason and evidence list.
"""


# Credential-scrubbing patterns applied to every command before it is sent to
# the Gemini API. Compiled once at module load to avoid repeated re.compile()
# calls inside the hot classification path.
_CRED_PATTERNS: List[tuple] = [
    (re.compile(r"(-p\s+)(\S+)"), r"\1[REDACTED]"),
    (re.compile(r"(--password(?:=|\s+))(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(password\s*=\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(token\s*=\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(api[_-]?key\s*=\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(Bearer\s+)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(-u\s+\S+:\s*)(\S+)"), r"\1[REDACTED]"),  # curl -u user:pass
]


def _scrub_command(cmd: str) -> str:
    """Apply all credential-scrubbing patterns to a command string."""
    for pattern, replacement in _CRED_PATTERNS:
        cmd = pattern.sub(replacement, cmd)
    return cmd


class GeminiClassifier:
    """
    LLM Intent Classifier utilizing the Google Gemini API via the official google-genai SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        enabled: Optional[bool] = None,
        client: Optional[Any] = None
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self.timeout = timeout if timeout is not None else settings.GEMINI_TIMEOUT
        self.enabled = enabled if enabled is not None else settings.GEMINI_ENABLED
        self._client = client

    def _get_client(self) -> Optional[Any]:
        """
        Lazily initializes the official google-genai Client.
        """
        if self._client is not None:
            return self._client

        if not self.enabled or not is_gemini_api_key_configured(self.api_key):
            return None

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            return self._client
        except Exception as e:
            logger.warning("Failed to initialize google-genai Client: %s", e)
            return None

    @staticmethod
    def sanitize_payload(
        event: NormalizedEvent,
        session_features: Optional[SessionFeatures] = None
    ) -> Dict[str, Any]:
        """
        Constructs a sanitized context payload, explicitly omitting authentication passwords,
        secrets, and raw honeypot hashes.
        """
        sanitized_command = event.command
        # Scrub all known credential patterns from the command before sending to Gemini.
        if sanitized_command:
            sanitized_command = _scrub_command(sanitized_command)

        payload: Dict[str, Any] = {
            "session_id": event.session_id,
            "event_type": event.event_type,
            "command": sanitized_command,
            "source_ip": event.source_ip,
            "protocol": event.protocol,
            "timestamp": event.timestamp.isoformat()
        }

        if session_features:
            payload["session_context"] = {
                "duration_seconds": session_features.duration_seconds,
                "total_events": session_features.total_events,
                "command_count": session_features.command_count,
                "unique_commands": session_features.unique_commands[-8:],  # last 8 unique commands
                "activity_rate": session_features.activity_rate,
                "login_failed_count": session_features.login_failed_count,
                "login_success_count": session_features.login_success_count
            }

        return payload

    def classify(
        self,
        event: NormalizedEvent,
        session_features: Optional[SessionFeatures] = None
    ) -> Optional[GeminiClassification]:
        """
        Submits sanitized telemetry to Gemini and returns validated GeminiClassification,
        or None if Gemini is disabled, unavailable, or fails.
        """
        client = self._get_client()
        if client is None:
            logger.debug("Gemini classification skipped: client unavailable or disabled")
            return None

        payload = self.sanitize_payload(event, session_features)
        prompt = (
            f"Analyze the following honeypot interaction telemetry and classify attacker intent and attack stage:\n"
            f"```json\n{json.dumps(payload, indent=2)}\n```"
        )

        try:
            from google.genai import types

            config_kwargs: Dict[str, Any] = dict(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=GeminiClassification,
                temperature=0.1,
            )
            # Enforce a hard per-request timeout so a hung LLM call cannot stall the
            # ingestion pipeline indefinitely. google-genai expects milliseconds.
            if self.timeout and self.timeout > 0:
                config_kwargs["http_options"] = types.HttpOptions(
                    timeout=int(self.timeout * 1000)
                )

            config = types.GenerateContentConfig(**config_kwargs)

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            raw_text = response.text if hasattr(response, "text") else str(response)
            if not raw_text:
                logger.warning("Empty response from Gemini API")
                return None

            data = json.loads(raw_text)
            validated = GeminiClassification.model_validate(data)
            return validated

        except json.JSONDecodeError as err:
            logger.warning("Failed to decode JSON response from Gemini: %s", err)
            return None
        except Exception as e:
            logger.warning("Gemini classification request failed: %s", e)
            return None
