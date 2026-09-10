"""
Models package for Intent-Aware Deception System.
"""

from backend.app.models.api import (
    DashboardStatsResponse,
    HealthResponse,
    IntentDistributionItem,
    PaginatedResponse,
    SeverityDistributionItem,
    TimelineBucketItem,
)
from backend.app.models.database import (
    AlertDoc,
    AttackerProfileDoc,
    StoredEventDoc,
    StoredSessionDoc,
)
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import EventFeatures, SessionFeatures
from backend.app.models.intent import (
    AttackStage,
    ClassificationSource,
    GeminiClassification,
    HybridClassification,
    IntentCategory,
    RuleClassification,
)
from backend.app.models.risk import RiskAssessment, RiskSeverity
from backend.app.models.session_intelligence import SessionIntelligence

__all__ = [
    "NormalizedEvent",
    "EventFeatures",
    "SessionFeatures",
    "IntentCategory",
    "AttackStage",
    "ClassificationSource",
    "RuleClassification",
    "GeminiClassification",
    "HybridClassification",
    "RiskSeverity",
    "RiskAssessment",
    "SessionIntelligence",
    "StoredEventDoc",
    "StoredSessionDoc",
    "AttackerProfileDoc",
    "AlertDoc",
    "HealthResponse",
    "DashboardStatsResponse",
    "PaginatedResponse",
    "IntentDistributionItem",
    "SeverityDistributionItem",
    "TimelineBucketItem",
]
