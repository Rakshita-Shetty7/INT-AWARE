"""
Random Forest Intrusion-Stage Classifier for Cyber Kill Chain & MITRE ATT&CK Mapping.

Classifies attacker commands and behavioral events into intrusion progression stages:
RECONNAISSANCE, INITIAL_ACCESS, DISCOVERY, CREDENTIAL_ACCESS, PRIVILEGE_ESCALATION,
EXECUTION, PERSISTENCE, EXFILTRATION, CLEANUP.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np

from backend.app.models.intent import AttackStage

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
DEFAULT_STAGE_RF_PATH = ARTIFACTS_DIR / "stage_random_forest.joblib"


class StageRandomForestClassifier:
    """
    Random Forest Classifier trained to map command strings to MITRE ATT&CK intrusion stages.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_STAGE_RF_PATH
        self._pipeline = None
        self._classes: List[str] = []
        self._metadata: Dict[str, Any] = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """Loads serialized Random Forest pipeline artifact."""
        if not self.model_path.exists():
            logger.info("Random Forest stage artifact not found at %s. Running in uncalibrated mode.", self.model_path)
            return

        try:
            bundle = joblib.load(self.model_path)
            self._pipeline = bundle.get("pipeline")
            self._metadata = bundle.get("metadata", {})
            if hasattr(self._pipeline, "classes_"):
                self._classes = [str(c) for c in self._pipeline.classes_]
            self._loaded = True
            logger.info("Loaded Random Forest stage classifier from %s", self.model_path)
        except Exception as e:
            logger.error("Failed to load Random Forest stage classifier from %s: %s", self.model_path, e)

    @property
    def is_available(self) -> bool:
        return self._loaded and self._pipeline is not None

    def classify_stage(self, cmd: str) -> Dict[str, Any]:
        """
        Classifies an input command into an AttackStage.

        Returns:
            stage: AttackStage enum string
            confidence: float (0.0 to 1.0)
            stage_distribution: Dict[str, float]
            source: str
        """
        if not self.is_available:
            return {
                "stage": AttackStage.UNKNOWN.value,
                "confidence": 0.0,
                "stage_distribution": {},
                "source": "fallback",
            }

        try:
            probs = self._pipeline.predict_proba([cmd])[0]
            best_idx = int(np.argmax(probs))
            best_stage = self._classes[best_idx]
            best_prob = float(probs[best_idx])

            dist = {self._classes[i]: round(float(probs[i]), 4) for i in range(len(self._classes))}

            return {
                "stage": best_stage,
                "confidence": round(best_prob, 4),
                "stage_distribution": dist,
                "source": "random_forest_stage",
            }
        except Exception as e:
            logger.warning("Stage classification error for '%s': %s", cmd, e)
            return {
                "stage": AttackStage.UNKNOWN.value,
                "confidence": 0.0,
                "stage_distribution": {},
                "source": "error_fallback",
            }


# Global singleton
stage_random_forest_classifier = StageRandomForestClassifier()
