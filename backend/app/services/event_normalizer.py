"""
Event Normalizer Service.
Transforms raw Cowrie JSON events into normalized, validated NormalizedEvent objects.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from backend.app.models.events import NormalizedEvent

logger = logging.getLogger(__name__)

# Canonical mapping of Cowrie event IDs to system event types
EVENT_TYPE_MAPPING = {
    "cowrie.session.connect": "session_connect",
    "cowrie.session.closed": "session_closed",
    "cowrie.client.version": "client_version",
    "cowrie.client.kex": "client_kex",
    "cowrie.client.size": "client_size",
    "cowrie.client.var": "client_var",
    "cowrie.login.success": "login_success",
    "cowrie.login.failed": "login_failed",
    "cowrie.command.input": "command_input",
    "cowrie.command.failed": "command_failed",
    "cowrie.session.params": "session_params",
    "cowrie.session.file_download": "file_download",
    "cowrie.session.file_upload": "file_upload",
    "cowrie.log.closed": "log_closed",
    "cowrie.direct-tcpip.request": "port_forward_request",
    "cowrie.direct-tcpip.data": "port_forward_data",
}


class EventNormalizer:
    """
    Normalizes heterogeneous Cowrie JSON logs into standardized NormalizedEvent instances.
    """

    @staticmethod
    def parse_timestamp(ts_value: Any) -> datetime:
        """
        Safely parses ISO8601 timestamps (including 'Z' or microsecond variants) to UTC datetime.
        """
        if isinstance(ts_value, datetime):
            if ts_value.tzinfo is None:
                return ts_value.replace(tzinfo=timezone.utc)
            return ts_value.astimezone(timezone.utc)

        if isinstance(ts_value, str):
            try:
                # Handle standard ISO8601 ending in Z
                clean_ts = ts_value.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception as e:
                logger.debug("Failed to parse ISO timestamp '%s': %s", ts_value, e)

        # Fallback to current UTC time
        return datetime.now(timezone.utc)

    @staticmethod
    def generate_deterministic_event_id(raw_event: Dict[str, Any], session_id: str, ts_str: str) -> str:
        """
        Generates a deterministic unique hash for an event to prevent duplicate processing.
        """
        eventid = raw_event.get("eventid", "")
        src_port = str(raw_event.get("src_port", ""))
        cmd = str(raw_event.get("input", ""))
        msg = str(raw_event.get("message", ""))
        unique_key = f"{session_id}|{ts_str}|{eventid}|{src_port}|{cmd}|{msg}"
        return hashlib.sha256(unique_key.encode("utf-8")).hexdigest()[:24]

    @classmethod
    def normalize(cls, raw: Union[str, Dict[str, Any]]) -> Optional[NormalizedEvent]:
        """
        Normalizes a raw Cowrie event dictionary or JSON string into a NormalizedEvent.
        Returns None if the event is unparseable or completely invalid.
        """
        if isinstance(raw, str):
            clean_str = raw.strip()
            if not clean_str:
                return None
            try:
                raw_dict = json.loads(clean_str)
            except json.JSONDecodeError as err:
                logger.warning("Failed to decode JSON line: %s", err)
                return None
        elif isinstance(raw, dict):
            raw_dict = raw
        else:
            logger.warning("Invalid raw event input type: %s", type(raw))
            return None

        if not isinstance(raw_dict, dict):
            return None

        # Extract core attributes
        raw_eventid = raw_dict.get("eventid")
        session_id = raw_dict.get("session")
        
        # If session_id is missing, generate fallback or discard
        if not session_id:
            session_id = "unknown_session"

        # Timestamp normalization
        raw_timestamp = raw_dict.get("timestamp")
        normalized_dt = cls.parse_timestamp(raw_timestamp)
        ts_str = normalized_dt.isoformat()

        # Map event type
        if raw_eventid in EVENT_TYPE_MAPPING:
            event_type = EVENT_TYPE_MAPPING[raw_eventid]
        elif isinstance(raw_eventid, str):
            event_type = raw_eventid.replace("cowrie.", "").replace(".", "_")
        else:
            event_type = "unknown"

        # Command extraction (Cowrie uses 'input' for commands)
        command = raw_dict.get("input")
        if command is not None:
            command = str(command).strip()

        # Source IP and port
        source_ip = raw_dict.get("src_ip")
        source_port = raw_dict.get("src_port")
        if source_port is not None:
            try:
                source_port = int(source_port)
            except (ValueError, TypeError):
                source_port = None

        # Protocol
        protocol = raw_dict.get("protocol")

        # Username extraction
        username = raw_dict.get("username")

        # Generate deterministic event_id
        event_id = cls.generate_deterministic_event_id(raw_dict, session_id, ts_str)

        return NormalizedEvent(
            event_id=event_id,
            timestamp=normalized_dt,
            session_id=str(session_id),
            source_ip=str(source_ip) if source_ip is not None else None,
            source_port=source_port,
            protocol=str(protocol) if protocol is not None else None,
            username=str(username) if username is not None else None,
            event_type=event_type,
            command=command,
            raw_event=raw_dict,
            collected_at=datetime.now(timezone.utc)
        )
