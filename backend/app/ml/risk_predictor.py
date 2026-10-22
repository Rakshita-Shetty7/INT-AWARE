"""
Gradient Boosting Threat Risk Predictor for Honeypot Events & Sessions.

Predicts continuous risk scores (0 to 100) and mapped severity categories (LOW, MEDIUM, HIGH, CRITICAL)
using Gradient Boosted Trees trained on structural features, intent vectors, and session velocity.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np

from backend.app.models.risk import RiskSeverity
from backend.app.ml.features import (
    extract_risk_features,
    SENSITIVE_REGEX,
    DESTRUCTIVE_REGEX,
    NETWORK_REGEX,
    PRIVESC_REGEX,
)
from backend.app.ml.labels import INTENT_CLASSES

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
DEFAULT_GB_RISK_PATH = ARTIFACTS_DIR / "risk_gradient_boosting.joblib"


class GradientBoostingRiskPredictor:
    """
    Gradient Boosted Regressor predicting threat risk scores and severity classifications.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_GB_RISK_PATH
        self._model = None
        self._metadata: Dict[str, Any] = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """Loads serialized Gradient Boosting regressor artifact."""
        if not self.model_path.exists():
            logger.info("Gradient Boosting risk artifact not found at %s. Running in heuristic mode.", self.model_path)
            return

        try:
            bundle = joblib.load(self.model_path)
            self._model = bundle.get("model")
            self._metadata = bundle.get("metadata", {})
            self._loaded = True
            logger.info("Loaded Gradient Boosting risk predictor from %s", self.model_path)
        except Exception as e:
            logger.error("Failed to load Gradient Boosting risk predictor from %s: %s", self.model_path, e)

    @property
    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    def map_severity(self, score: int) -> RiskSeverity:
        """Maps 0-100 risk score into standardized severity categories."""
        if score < 25:
            return RiskSeverity.LOW
        elif score < 50:
            return RiskSeverity.MEDIUM
        elif score < 75:
            return RiskSeverity.HIGH
        else:
            return RiskSeverity.CRITICAL

    def predict_risk(
        self,
        cmd: str,
        intent: Optional[str] = None,
        session_command_count: int = 1,
        failed_logins: int = 0,
        session_duration_s: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Predicts threat risk score (0-100) and severity for an event in session context.
        """
        # Create intent one-hot vector
        intent_vec = np.zeros(10, dtype=np.float32)
        if intent and intent in INTENT_CLASSES:
            idx = INTENT_CLASSES.index(intent)
            intent_vec[idx] = 1.0

        features = extract_risk_features(
            cmd=cmd,
            intent_onehot=intent_vec,
            session_command_count=session_command_count,
            failed_logins=failed_logins,
            session_duration_s=session_duration_s,
        )

        factors = []
        if failed_logins > 0:
            factors.append(f"Session observed {failed_logins} failed authentication attempt(s)")
        if SENSITIVE_REGEX.search(cmd):
            factors.append("Targeting high-value credentials or critical configuration")
        if DESTRUCTIVE_REGEX.search(cmd):
            factors.append("Destructive filesystem or process manipulation primitive")
        if NETWORK_REGEX.search(cmd):
            factors.append("Outbound communication or lateral data exfiltration utility")
        if PRIVESC_REGEX.search(cmd):
            factors.append("Root privilege escalation attempt")

        if not self.is_available:
            # Baseline deterministic calculation
            base_score = 15
            if intent in ["EXPLOITATION", "EXFILTRATION", "PRIVILEGE_ESCALATION"]:
                base_score = 75
            elif intent in ["CREDENTIAL_ACCESS", "PERSISTENCE", "EXECUTION"]:
                base_score = 55
            elif intent in ["DISCOVERY", "RECONNAISSANCE"]:
                base_score = 30

            score = min(100, base_score + failed_logins * 5 + len(factors) * 10)
            severity = self.map_severity(score)
            return {
                "risk_score": int(score),
                "severity": severity,
                "contributing_factors": factors,
                "source": "heuristic_fallback",
            }

        X = features.reshape(1, -1)
        pred_raw = float(self._model.predict(X)[0])
        score = int(np.clip(round(pred_raw), 0, 100))
        severity = self.map_severity(score)

        return {
            "risk_score": score,
            "severity": severity,
            "contributing_factors": factors,
            "raw_score": round(pred_raw, 2),
            "source": "gradient_boosting",
        }


# Global singleton
gradient_boosting_risk_predictor = GradientBoostingRiskPredictor()
