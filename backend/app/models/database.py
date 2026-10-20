"""
MongoDB Document Models for Events, Sessions, Attacker Profiles, and Alerts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.features import EventFeatures
from backend.app.models.intent import AttackStage, ClassificationSource, IntentCategory
from backend.app.models.risk import RiskSeverity


class StoredEventDoc(BaseModel):
    """
    Schema for individual honeypot events persisted in the 'events' collection.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    event_id: str = Field(..., description="Deterministic unique identifier")
    timestamp: datetime = Field(..., description="Normalized UTC timestamp of event")
    session_id: str = Field(..., description="Associated Cowrie session ID")
    source_ip: Optional[str] = Field(None, description="Attacker IP address")
    source_port: Optional[int] = Field(None, description="Attacker source port")
    protocol: Optional[str] = Field(None, description="Connection protocol (ssh/telnet)")
    username: Optional[str] = Field(None, description="Attempted or authenticated username")
    event_type: str = Field(..., description="Canonical event classification")
    command: Optional[str] = Field(None, description="Sanitized command string executed")
    behavioral_features: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted event features")
    intent: IntentCategory = Field(..., description="Classified attacker intent")
    attack_stage: AttackStage = Field(..., description="Identified attack stage")
    confidence: float = Field(..., description="Confidence of classification (0.0 - 1.0)")
    classification_source: ClassificationSource = Field(..., description="RULE, ML, GEMINI, HYBRID, or FALLBACK")
    rule_evidence: List[str] = Field(default_factory=list, description="Evidence from heuristic rule matches")
    ml_intent: Optional[IntentCategory] = Field(None, description="Intent predicted by the ML model (if available)")
    ml_confidence: Optional[float] = Field(None, description="ML model calibrated confidence (if available)")
    ml_model_name: Optional[str] = Field(None, description="Name of the ML model that produced ml_intent")
    ml_evidence: List[str] = Field(default_factory=list, description="Explanation from the ML model")
    ai_reason: Optional[str] = Field(None, description="Reasoning provided by Gemini AI")
    ai_evidence: List[str] = Field(default_factory=list, description="Key markers identified by Gemini AI")
    uncertainty_score: Optional[float] = Field(0.0, description="Epistemic uncertainty score")
    is_novel: Optional[bool] = Field(False, description="Whether command was novel/out-of-distribution")
    should_abstain: Optional[bool] = Field(False, description="Whether classifier recommended abstention")
    risk_score: int = Field(0, ge=0, le=100, description="Calculated event threat score")
    severity: RiskSeverity = Field(RiskSeverity.LOW, description="Categorical threat severity")
    raw_event: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Sanitized original event metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Database insert timestamp")


class StoredSessionDoc(BaseModel):
    """
    Schema for session intelligence profiles persisted in the 'sessions' collection.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    session_id: str = Field(..., description="Unique session identifier")
    source_ip: Optional[str] = Field(None, description="Attacker IP address")
    protocol: Optional[str] = Field(None, description="Protocol used")
    username: Optional[str] = Field(None, description="Target username")
    first_seen: datetime = Field(..., description="Timestamp of session start")
    last_seen: datetime = Field(..., description="Timestamp of latest event in session")
    duration: float = Field(0.0, description="Active session duration in seconds")
    total_events: int = Field(0, description="Total events count")
    command_count: int = Field(0, description="Total commands executed")
    unique_command_count: int = Field(0, description="Count of distinct commands")
    unique_commands: List[str] = Field(default_factory=list, description="List of distinct commands")
    login_attempt_count: int = Field(0, description="Count of login attempts")
    intent_sequence: List[str] = Field(default_factory=list, description="Chronological sequence of intents")
    stage_sequence: List[str] = Field(default_factory=list, description="Chronological sequence of stages")
    dominant_intent: IntentCategory = Field(..., description="Primary intent observed")
    current_attack_stage: AttackStage = Field(..., description="Current/furthest attack stage")
    risk_score: int = Field(0, ge=0, le=100, description="Aggregated session risk score")
    severity: RiskSeverity = Field(RiskSeverity.LOW, description="Aggregated session severity")
    confidence: float = Field(0.0, description="Confidence in profile")
    key_evidence: List[str] = Field(default_factory=list, description="Aggregated behavioral evidence")
    is_closed: bool = Field(False, description="Whether session is terminated")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")


class AttackerProfileDoc(BaseModel):
    """
    Schema for persistent attacker host profiles in the 'attackers' collection.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    source_ip: str = Field(..., description="Attacker IP address (Primary Key)")
    first_seen: datetime = Field(..., description="Timestamp of earliest interaction")
    last_seen: datetime = Field(..., description="Timestamp of most recent interaction")
    total_sessions: int = Field(0, description="Number of sessions originating from this IP")
    total_events: int = Field(0, description="Total event count from this IP")
    average_risk: float = Field(0.0, description="Average risk score across all sessions")
    maximum_risk: int = Field(0, ge=0, le=100, description="Maximum risk score observed")
    dominant_intent: IntentCategory = Field(IntentCategory.OTHER, description="Overall dominant intent")
    current_stage: AttackStage = Field(AttackStage.UNKNOWN, description="Furthest attack stage reached")
    severity: RiskSeverity = Field(RiskSeverity.LOW, description="Overall threat severity")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last profile update timestamp")


class AlertDoc(BaseModel):
    """
    Schema for high-severity security alerts in the 'alerts' collection.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    alert_id: str = Field(..., description="Unique alert identifier")
    session_id: str = Field(..., description="Session triggering the alert")
    source_ip: Optional[str] = Field(None, description="Attacker IP address")
    timestamp: datetime = Field(..., description="Timestamp when condition occurred")
    severity: RiskSeverity = Field(..., description="Session severity at alert time (HIGH or CRITICAL)")
    risk_score: int = Field(..., ge=50, le=100, description="Session cumulative risk score at alert time. The exact firing threshold is policy (settings.ALERT_RISK_THRESHOLD, default 75); this ge=50 bound is only a data-validity floor so alerts are never sub-HIGH.")
    intent: IntentCategory = Field(..., description="Triggering intent category")
    attack_stage: AttackStage = Field(..., description="Triggering attack stage")
    reason: str = Field(..., description="Explanation of why the alert was generated")
    status: str = Field("OPEN", description="Alert status (OPEN, INVESTIGATING, RESOLVED, DISMISSED)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Alert creation timestamp")
