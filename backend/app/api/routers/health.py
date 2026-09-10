"""
Health check router.

Reports the status of every subsystem — MongoDB, the trained ML classifier, the
optional Gemini semantic layer, the deterministic rule engine, and the Cowrie log
feed — so operators and the dashboard can confirm the full pipeline is live.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from backend.app.config import is_gemini_api_key_configured, settings
from backend.app.database.mongodb import mongodb_manager
from backend.app.ml.intent_ml_classifier import ml_intent_classifier
from backend.app.models.api import HealthResponse

router = APIRouter(tags=["Health"])

_METRICS_PATH = Path(__file__).resolve().parents[3] / "app" / "ml" / "artifacts" / "metrics.json"


@lru_cache(maxsize=1)
def _ml_accuracy() -> float | None:
    """Reads the honest held-out accuracy from the training metrics (cached)."""
    try:
        data = json.loads(_METRICS_PATH.read_text(encoding="utf-8"))
        return data.get("primary_evaluation", {}).get("accuracy")
    except Exception:
        return None


@router.get("/health", response_model=HealthResponse, summary="System Health Check")
def health_check():
    """
    Checks the FastAPI backend, MongoDB, ML model, Gemini, rule engine, and Cowrie feed.
    """
    is_db_connected = mongodb_manager.check_health()

    ml_status = {
        "available": ml_intent_classifier.available,
        "model_name": ml_intent_classifier._model_name if ml_intent_classifier.available else None,
        "classes": len(ml_intent_classifier._classes) if ml_intent_classifier.available else 0,
        "accuracy": _ml_accuracy(),
    }

    collector_path = settings.COWRIE_LOG_PATH
    cowrie_present = False
    try:
        cowrie_present = os.path.exists(collector_path) and os.path.getsize(collector_path) >= 0
    except Exception:
        cowrie_present = False

    return HealthResponse(
        status="healthy" if is_db_connected else "degraded",
        database="connected" if is_db_connected else "disconnected",
        ml_model=ml_status,
        gemini_enabled=bool(settings.GEMINI_ENABLED and is_gemini_api_key_configured(settings.GEMINI_API_KEY)),
        rule_engine_enabled=settings.RULE_ENGINE_ENABLED,
        cowrie_log_present=cowrie_present,
        collector_path=collector_path,
    )
