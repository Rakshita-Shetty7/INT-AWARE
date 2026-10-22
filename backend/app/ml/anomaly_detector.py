"""
Isolation Forest Anomaly & Unknown Behavior Detector for Cowrie Honeypot Events.

Detects out-of-distribution shell commands, obfuscated payloads, memory injection,
and atypical attacker behavior using an Isolation Forest trained on normal telemetry.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import joblib

from backend.app.ml.features import extract_command_features

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
DEFAULT_ISOFOREST_PATH = ARTIFACTS_DIR / "isolation_forest.joblib"


class CowrieAnomalyDetector:
    """
    Unsupervised / Semi-supervised Isolation Forest Anomaly Detector.
    Scores command strings and flags novel, anomalous, or out-of-distribution attacker activity.
    """

    def __init__(self, model_path: Optional[Path] = None, anomaly_threshold: float = 0.65):
        self.model_path = Path(model_path) if model_path else DEFAULT_ISOFOREST_PATH
        self.anomaly_threshold = anomaly_threshold
        self._model = None
        self._scaler = None
        self._metadata: Dict[str, Any] = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """Loads serialized Isolation Forest artifact and scaler."""
        if not self.model_path.exists():
            logger.info("Isolation Forest artifact not found at %s. Running in uncalibrated mode.", self.model_path)
            return

        try:
            bundle = joblib.load(self.model_path)
            self._model = bundle.get("model")
            self._scaler = bundle.get("scaler")
            self._metadata = bundle.get("metadata", {})
            self._loaded = True
            logger.info("Loaded Isolation Forest model from %s", self.model_path)
        except Exception as e:
            logger.error("Failed to load Isolation Forest from %s: %s", self.model_path, e)

    @property
    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    def score_command(self, cmd: str) -> Dict[str, Any]:
        """
        Evaluates a command string for anomalousness and out-of-distribution structure.

        Returns:
            anomaly_score: float in [0.0, 1.0] (higher means more anomalous)
            is_anomaly: bool
            factors: list of human-interpretable reasons
        """
        raw_feat = extract_command_features(cmd)
        factors: List[str] = []

        # Structural rule-assisted heuristic explanations
        if raw_feat[1] > 0.5:
            factors.append("Hexadecimal or escaped character sequence")
        if raw_feat[2] > 0.5:
            factors.append("Base64 encoded binary payload block")
        if raw_feat[3] > 0.5:
            factors.append("Critical weaponization, exploit, or evasion primitive")
        if raw_feat[4] > 0.7:
            factors.append(f"Unusually high Shannon entropy ({raw_feat[4]*8.0:.2f} bits/byte)")

        if not self.is_available:
            heuristic_score = min(1.0, len(factors) * 0.35 + raw_feat[4] * 0.3)
            return {
                "anomaly_score": round(float(heuristic_score), 4),
                "is_anomaly": heuristic_score >= 0.5,
                "factors": factors,
                "source": "heuristic_fallback",
            }

        # Vector scoring
        X = raw_feat.reshape(1, -1)
        if self._scaler is not None:
            X = self._scaler.transform(X)

        raw_score = float(self._model.score_samples(X)[0])
        calibrated_th = float(self._metadata.get("calibrated_threshold", -0.4906))

        # Calibrated score: inlier/normal maps to < 0.5, outlier/anomaly maps to >= 0.5
        normalized_score = float(np.clip((calibrated_th - raw_score) / 0.15 + 0.5, 0.0, 1.0))
        is_anom = raw_score < calibrated_th or normalized_score >= 0.5 or raw_feat[3] > 0.5

        if is_anom and not factors:
            factors.append("Atypical token distribution and parameter complexity")

        return {
            "anomaly_score": round(normalized_score, 4),
            "is_anomaly": is_anom,
            "raw_decision_score": round(raw_score, 4),
            "factors": factors,
            "source": "isolation_forest",
        }


# Global singleton
cowrie_anomaly_detector = CowrieAnomalyDetector()
