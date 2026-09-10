"""
Feature Models for Behavioral Analysis and Session Profiling.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EventFeatures(BaseModel):
    """
    Behavioral feature vectors extracted from individual events.
    """
    session_id: str = Field(..., description="Session identifier")
    event_type: str = Field(..., description="Canonical event type")
    has_command: bool = Field(False, description="Whether the event contains a shell command")
    command: Optional[str] = Field(None, description="Command string if present")
    command_length: int = Field(0, description="Character length of command")
    command_token_count: int = Field(0, description="Number of whitespace-delimited tokens in command")
    timestamp: datetime = Field(..., description="Timestamp of the event")


class SessionFeatures(BaseModel):
    """
    Aggregated behavioral feature profile maintaining state for a distinct session.
    """
    session_id: str = Field(..., description="Unique session identifier")
    source_ip: Optional[str] = Field(None, description="Attacker source IP address")
    protocol: Optional[str] = Field(None, description="Protocol used in session")
    username: Optional[str] = Field(None, description="Last or authenticated username")
    first_seen: Optional[datetime] = Field(None, description="Timestamp of first event in session")
    last_seen: Optional[datetime] = Field(None, description="Timestamp of most recent event in session")
    duration_seconds: float = Field(0.0, description="Total active duration of session in seconds")
    total_events: int = Field(0, description="Total count of events received for this session")
    command_count: int = Field(0, description="Total number of commands executed")
    unique_commands: List[str] = Field(default_factory=list, description="List of unique commands executed")
    unique_command_count: int = Field(0, description="Count of distinct unique commands executed")
    login_attempt_count: int = Field(0, description="Total login attempts in this session")
    login_success_count: int = Field(0, description="Count of successful logins")
    login_failed_count: int = Field(0, description="Count of failed logins")
    event_types: Dict[str, int] = Field(default_factory=dict, description="Histogram of event occurrences by type")
    distinct_event_types_count: int = Field(0, description="Number of distinct event types observed")
    commands: List[str] = Field(default_factory=list, description="Chronological sequence of commands executed")
    command_intervals: List[float] = Field(default_factory=list, description="Delta seconds between successive commands")
    average_command_interval: Optional[float] = Field(None, description="Average seconds between commands")
    activity_rate: float = Field(0.0, description="Overall event activity rate in events per second")
    command_frequency: float = Field(0.0, description="Command execution rate in commands per second")
    is_closed: bool = Field(False, description="Whether the session has terminated")
