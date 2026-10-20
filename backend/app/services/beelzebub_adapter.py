"""
Beelzebub Honeypot Telemetry Ingestion Adapter.

Parses, validates, and normalizes telemetry events emitted by the Beelzebub
honeypot runtime (SSH terminal emulation, HTTP decoy listeners, TCP probes)
into INT-AWARE's canonical NormalizedEvent schema.

Maintains strict event provenance, distinguishes Cowrie from Beelzebub telemetry,
and guarantees seamless integration with the 10-Class Intent Classifier,
Markov Sequence Transition Engine, and Risk Engine.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from backend.app.models.events import NormalizedEvent

logger = logging.getLogger(__name__)


class BeelzebubRawEvent(BaseModel):
    """Schema representing an incoming event from the Beelzebub honeypot runtime."""
    session_id: Optional[str] = Field(None, alias="sessionID")
    source_ip: Optional[str] = Field(None, alias="sourceIp")
    source_port: Optional[int] = Field(None, alias="sourcePort")
    destination_port: Optional[int] = Field(None, alias="destPort")
    protocol: Optional[str] = Field("ssh", alias="protocol")
    event_type: Optional[str] = Field(None, alias="eventType")
    command: Optional[str] = Field(None, alias="command")
    username: Optional[str] = Field(None, alias="username")
    password: Optional[str] = Field(None, alias="password")
    client_version: Optional[str] = Field(None, alias="clientVersion")
    status: Optional[str] = Field(None, alias="status")
    timestamp: Optional[str] = Field(None, alias="timestamp")


class BeelzebubAdapter:
    """
    Normalizes Beelzebub JSON events into INT-AWARE's canonical data model.
    """

    @staticmethod
    def _generate_event_id(session_id: str, timestamp_str: str, command_or_type: str) -> str:
        """Generates a deterministic unique ID for the event."""
        payload = f"beelzebub:{session_id}:{timestamp_str}:{command_or_type}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

    @classmethod
    def normalize(cls, raw: Dict[str, Any]) -> Optional[NormalizedEvent]:
        """
        Transforms a raw Beelzebub dictionary into a NormalizedEvent.
        """
        try:
            # Extract core fields with aliases
            session_id = str(raw.get("sessionID") or raw.get("session_id") or "beelzebub_anonymous")
            source_ip = raw.get("sourceIp") or raw.get("source_ip") or "127.0.0.1"
            source_port = int(raw.get("sourcePort") or raw.get("source_port") or 0)
            protocol = str(raw.get("protocol") or "ssh").lower()
            username = raw.get("username") or "root"
            command = raw.get("command")
            event_type = raw.get("eventType") or raw.get("event_type")

            # Determine canonical event_type
            if command:
                canonical_type = "command_input"
            elif event_type in ["login", "login_attempt", "auth"]:
                canonical_type = "login_success" if raw.get("status") == "success" else "login_failed"
            elif event_type in ["connect", "session_start"]:
                canonical_type = "session_connect"
            elif event_type in ["disconnect", "session_end"]:
                canonical_type = "session_disconnect"
            else:
                canonical_type = "command_input" if command else "generic_event"

            # Parse timestamp
            raw_ts = raw.get("timestamp")
            if raw_ts:
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.now(timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            event_id = cls._generate_event_id(session_id, ts.isoformat(), command or canonical_type)

            # Scrub passwords from raw metadata
            sanitized_raw = dict(raw)
            if "password" in sanitized_raw:
                sanitized_raw["password"] = "[REDACTED]"
            sanitized_raw["telemetry_source"] = "beelzebub"

            return NormalizedEvent(
                event_id=event_id,
                timestamp=ts,
                session_id=f"bz_{session_id}",
                source_ip=source_ip,
                source_port=source_port if source_port > 0 else 2222,
                protocol=protocol,
                username=username,
                event_type=canonical_type,
                command=command.strip() if command else None,
                raw_event=sanitized_raw,
            )
        except Exception as e:
            logger.warning("[BEELZEBUB ADAPTER] Failed to normalize event: %s (raw=%s)", e, raw)
            return None


# Global singleton
beelzebub_adapter = BeelzebubAdapter()
