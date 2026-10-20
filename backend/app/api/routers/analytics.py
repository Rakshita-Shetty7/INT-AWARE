"""
Analytics REST router.
Provides endpoints for Intent Distribution, Threat Severity, Attack Timeline, Stage Distribution,
Risk Score Distribution, and Intent x Risk Matrix Heatmap.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel as PydanticBaseModel

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


@router.get("/models", summary="Deployed Model Registry and Integrity Status")
def get_model_registry_status() -> Dict[str, Any]:
    """
    Returns registered model versions, hyperparameters, benchmark metrics, and artifact SHA-256 integrity status.
    """
    from backend.app.ml.registry import model_registry
    is_valid, msg = model_registry.verify_active_artifact_integrity()
    return {
        "active_model": model_registry.get_active_model(),
        "integrity_check": {"verified": is_valid, "message": msg},
        "all_models": model_registry.list_models(),
    }


@router.get("/drift", summary="Real-Time Concept Drift and PSI Report")
def get_drift_report() -> Dict[str, Any]:
    """
    Returns sliding-window Population Stability Index (PSI), prediction entropy, novelty rate, and drift status.
    """
    from backend.app.ml.drift_monitor import drift_monitor
    report = drift_monitor.compute_drift()
    return report.model_dump()


class TestCommandRequest(PydanticBaseModel):
    command: str


@router.post("/drift/test-command", summary="Evaluate Single Command for Drift & Novelty")
def test_command_drift(req: TestCommandRequest) -> Dict[str, Any]:
    """
    Evaluates a candidate command string against the runtime ML model to determine
    predicted intent, Shannon entropy, vocabulary novelty score, and abstention recommendation.
    """
    from backend.app.ml.intent_ml_classifier import ml_intent_classifier
    classification = ml_intent_classifier.classify(req.command)
    if not classification:
        return {
            "command": req.command,
            "status": "ML_UNAVAILABLE",
            "message": "ML model artifact is not loaded or command was empty.",
        }
    return {
        "command": req.command,
        "predicted_intent": str(classification.intent),
        "attack_stage": str(classification.attack_stage),
        "confidence": classification.confidence,
        "entropy": classification.entropy,
        "novelty_score": classification.novelty_score,
        "is_novel": classification.is_novel,
        "should_abstain": classification.should_abstain,
        "top_predictions": classification.top_predictions,
        "evidence": classification.evidence,
    }


@router.get("/campaign-graph", summary="Attack Campaign Relationship Graph")
def get_campaign_graph(
    persistence: PersistenceService = Depends(get_persistence_service)
) -> Dict[str, Any]:
    """
    Returns an evidence-backed relationship graph connecting Threat Actor IPs,
    Sessions, MITRE ATT&CK techniques, and observed indicators with cluster assignments.
    """
    from backend.app.services.campaign_graph import campaign_graph_engine
    sessions, _ = persistence.get_sessions(limit=100)
    attackers, _ = persistence.get_attackers(limit=100)
    events, _ = persistence.get_events(limit=200)
    graph_res = campaign_graph_engine.build_graph(sessions, attackers, events)
    return graph_res.model_dump()

