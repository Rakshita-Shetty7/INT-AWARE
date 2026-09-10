"""
Analytics REST router.
Provides endpoints for Intent Distribution, Threat Severity, Attack Timeline, Stage Distribution,
Risk Score Distribution, and Intent x Risk Matrix Heatmap.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_persistence_service
from backend.app.models.api import (
    IntentDistributionItem,
    SeverityDistributionItem,
    TimelineBucketItem,
)
from backend.app.services.persistence_service import PersistenceService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/intents", response_model=List[IntentDistributionItem], summary="Intent Analytics Distribution")
def get_intent_analytics(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns aggregated counts and percentage breakdowns across all classified intent categories.
    """
    items = persistence.get_intent_analytics()
    return [IntentDistributionItem(**i) for i in items]


@router.get("/severity", response_model=List[SeverityDistributionItem], summary="Threat Severity Breakdown")
def get_severity_analytics(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns distribution of risk severity categories (LOW, MEDIUM, HIGH, CRITICAL).
    """
    items = persistence.get_severity_analytics()
    return [SeverityDistributionItem(**i) for i in items]


@router.get("/timeline", response_model=List[TimelineBucketItem], summary="Attack Telemetry Timeline")
def get_timeline_analytics(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns chronological time buckets with event and session volumes for interactive graphing.
    """
    items = persistence.get_timeline_analytics()
    return [TimelineBucketItem(**i) for i in items]


@router.get("/stages", response_model=List[Dict[str, Any]], summary="Attack Stage Analytics")
def get_stage_analytics(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns aggregated distribution of MITRE attack stages reached across all honeypot sessions.
    """
    return persistence.get_stage_analytics()


@router.get("/risk-distribution", response_model=List[Dict[str, Any]], summary="Risk Score Distribution Buckets")
def get_risk_distribution(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns session counts and percentages distributed across standardized threat risk tiers (0-24, 25-49, 50-74, 75-100).
    """
    return persistence.get_risk_distribution()


@router.get("/heatmap", response_model=List[Dict[str, Any]], summary="Intent x Risk Heatmap")
def get_risk_intent_heatmap(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns cross-dimensional matrix correlating intent categories with average risk and severity distribution.
    """
    return persistence.get_risk_intent_heatmap()
