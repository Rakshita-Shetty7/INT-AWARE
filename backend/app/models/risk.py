"""
Risk Assessment and Severity Models.
"""

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class RiskSeverity(str, Enum):
    """
    Standardized threat severity levels mapped from deterministic risk scores.
    """
    LOW = "LOW"           # 0 - 24
    MEDIUM = "MEDIUM"     # 25 - 49
    HIGH = "HIGH"         # 50 - 74
    CRITICAL = "CRITICAL" # 75 - 100


class RiskAssessment(BaseModel):
    """
    Deterministic risk evaluation result for an event or aggregated session.
    """
    model_config = ConfigDict(use_enum_values=True)

    risk_score: int = Field(..., ge=0, le=100, description="Calculated threat risk score clamped between 0 and 100")
    severity: RiskSeverity = Field(..., description="Mapped categorical severity level")
    contributing_factors: List[str] = Field(default_factory=list, description="List of behavioral factors contributing to the score")
    calculation_details: Dict[str, Any] = Field(default_factory=dict, description="Transparent breakdown of the weight calculations")
