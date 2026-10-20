"""
Normalized Event Models for Cowrie Honeypot Ingestion.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class NormalizedEvent(BaseModel):
    """
    Standardized schema for all ingested honeypot events.
    Preserves raw event integrity while exposing normalized fields for behavioral processing.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_id: str = Field(..., description="Unique deterministic identifier for the event")
    timestamp: datetime = Field(..., description="Normalized UTC timestamp of event occurrence")
    session_id: str = Field(..., description="Cowrie session identifier")
    source_ip: Optional[str] = Field(None, description="Attacker source IP address")
    source_port: Optional[int] = Field(None, description="Attacker source port")
    protocol: Optional[str] = Field(None, description="Protocol used (e.g. ssh, telnet)")
    username: Optional[str] = Field(None, description="Username attempted or authenticated")
    event_type: str = Field(..., description="Normalized canonical event classification")
    command: Optional[str] = Field(None, description="Command string executed by attacker if applicable")
    raw_event: Dict[str, Any] = Field(default_factory=dict, description="Original raw Cowrie JSON event")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Collector ingestion timestamp (UTC)")
