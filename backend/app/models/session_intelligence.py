"""
Session Intelligence Profile Model.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.models.risk import RiskSeverity


class SessionIntelligence(BaseModel):
    """
    Holistic behavioral profile capturing attacker intent progression and threat level.
    """
    model_config = ConfigDict(use_enum_values=True)

    session_id: str = Field(..., description="Unique session identifier")
    source_ip: Optional[str] = Field(None, description="Attacker source IP address")
    dominant_intent: IntentCategory = Field(..., description="Most prominent intent observed across the session")
    current_attack_stage: AttackStage = Field(..., description="Furthest or current attack lifecycle stage")
    intent_sequence: List[IntentCategory] = Field(default_factory=list, description="Chronological sequence of classified intents")
    stage_sequence: List[AttackStage] = Field(default_factory=list, description="Chronological sequence of attack stages")
    risk_score: int = Field(0, ge=0, le=100, description="Overall aggregated session risk score (0-100)")
    severity: RiskSeverity = Field(RiskSeverity.LOW, description="Aggregated threat severity")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in the session intelligence assessment")
    key_evidence: List[str] = Field(default_factory=list, description="Top behavioral evidence items identified")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of latest profile update")
