"""
API Request and Response Models.
Provides strongly-typed schemas for REST API endpoints and pagination wrappers.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    """
    Service health check response, including the status of every subsystem so the
    dashboard (and operators) can confirm the full pipeline is live.
    """
    status: str = Field("healthy", description="Overall system health status")
    database: str = Field(..., description="MongoDB connection state (connected / disconnected)")
    ml_model: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trained ML classifier status {available, model_name, accuracy, classes}",
    )
    gemini_enabled: bool = Field(False, description="Whether the optional Gemini semantic layer is active")
    rule_engine_enabled: bool = Field(True, description="Whether the deterministic rule engine is active")
    cowrie_log_present: bool = Field(False, description="Whether the Cowrie honeypot JSON log is readable")
    collector_path: str = Field("", description="Path the ingestion collector is tailing")
    version: str = Field("1.0.0", description="API version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DashboardStatsResponse(BaseModel):
    """
    Summary metrics displayed on the executive security dashboard.
    """
    total_sessions: int = Field(0, description="Total attacker sessions captured")
    active_sessions: int = Field(0, description="Currently open/active attacker sessions")
    total_events: int = Field(0, description="Total telemetry events processed")
    total_attackers: int = Field(0, description="Count of distinct attacker source IP addresses")
    high_risk_sessions: int = Field(0, description="Sessions with risk score 50-74 (HIGH)")
    critical_sessions: int = Field(0, description="Sessions with risk score 75-100 (CRITICAL)")
    open_alerts: int = Field(0, description="Count of unresolved high-severity alerts")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic pagination envelope ensuring safe limits on database query returns.
    """
    items: List[T] = Field(default_factory=list, description="Paginated records for current page")
    total: int = Field(..., description="Total count of matching records across all pages")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    limit: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of available pages")


class IntentDistributionItem(BaseModel):
    """
    Intent category frequency breakdown item.
    """
    intent: str = Field(..., description="Intent Category name")
    count: int = Field(..., description="Number of events classified with this intent")
    percentage: float = Field(..., description="Percentage of total classified events")


class SeverityDistributionItem(BaseModel):
    """
    Severity distribution breakdown item.
    """
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    count: int = Field(..., description="Count of events/sessions in this severity tier")
    percentage: float = Field(..., description="Percentage of total events/sessions")


class TimelineBucketItem(BaseModel):
    """
    Time-series bucket item for interactive attack trend graphs.
    """
    timestamp: str = Field(..., description="ISO8601 bucket time interval")
    event_count: int = Field(0, description="Number of events occurred in this time window")
    session_count: int = Field(0, description="Distinct sessions active in this time window")
    max_risk: int = Field(0, description="Peak risk score observed in this time window")
