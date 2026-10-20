"""
Runtime Concept Drift & Population Stability Index (PSI) Monitor.

Monitors real-time distribution shift between offline training class priors
and live honeypot prediction streams to detect model staleness and emerging attack campaigns.
"""

from __future__ import annotations

import collections
import logging
import math
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.intent import IntentCategory

logger = logging.getLogger(__name__)

# Baseline class distribution from the verified training corpus
TRAIN_CLASS_PRIORS: Dict[str, float] = {
    IntentCategory.RECONNAISSANCE.value: 0.197,
    IntentCategory.DISCOVERY.value: 0.178,
    IntentCategory.CREDENTIAL_ACCESS.value: 0.124,
    IntentCategory.EXECUTION.value: 0.141,
    IntentCategory.PRIVILEGE_ESCALATION.value: 0.116,
    IntentCategory.PERSISTENCE.value: 0.082,
    IntentCategory.EXPLOITATION.value: 0.065,
    IntentCategory.EXFILTRATION.value: 0.043,
    IntentCategory.CLEANUP.value: 0.035,
    IntentCategory.OTHER.value: 0.019,
}


class DriftReport(BaseModel):
    """Formal drift evaluation report over sliding observation window."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window_size: int = Field(..., description="Number of events in current sliding evaluation window")
    psi_score: float = Field(..., ge=0.0, description="Population Stability Index score")
    drift_status: str = Field(..., description="STABLE, MODERATE_DRIFT, or SIGNIFICANT_DRIFT")
    mean_prediction_entropy: float = Field(0.0, description="Mean Shannon entropy across observed window")
    novelty_rate: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of events flagged as novel/OOD")
    observed_distribution: Dict[str, float] = Field(default_factory=dict)
    baseline_distribution: Dict[str, float] = Field(default_factory=dict)
    recommendation: str = Field(..., description="Actionable recommendation for SOC / ML engineer")


class ConceptDriftMonitor:
    """
    Sliding-window distribution drift tracker computing Population Stability Index (PSI)
    and prediction entropy statistics.
    """

    def __init__(self, window_capacity: int = 500, min_eval_samples: int = 20):
        self.window_capacity = window_capacity
        self.min_eval_samples = min_eval_samples
        self._intent_window: Deque[str] = collections.deque(maxlen=window_capacity)
        self._entropy_window: Deque[float] = collections.deque(maxlen=window_capacity)
        self._novelty_window: Deque[bool] = collections.deque(maxlen=window_capacity)
        self.baseline_priors = TRAIN_CLASS_PRIORS

    def record_prediction(self, intent: str, entropy: float = 0.0, is_novel: bool = False) -> None:
        """Records an incoming prediction into the bounded sliding window."""
        self._intent_window.append(intent)
        self._entropy_window.append(max(0.0, float(entropy)))
        self._novelty_window.append(bool(is_novel))

    def compute_drift(self) -> DriftReport:
        """
        Calculates the Population Stability Index (PSI) against training priors.
        """
        n = len(self._intent_window)
        if n < self.min_eval_samples:
            return DriftReport(
                window_size=n,
                psi_score=0.0,
                drift_status="INSUFFICIENT_DATA",
                mean_prediction_entropy=0.0,
                novelty_rate=0.0,
                observed_distribution={},
                baseline_distribution=self.baseline_priors,
                recommendation=f"Accumulating observation telemetry ({n}/{self.min_eval_samples} samples required).",
            )

        # Compute empirical frequencies
        counts: Dict[str, int] = collections.Counter(self._intent_window)
        observed_priors = {k: counts.get(k, 0) / n for k in self.baseline_priors}

        # Calculate Population Stability Index (PSI)
        # PSI = sum( (Actual - Expected) * ln(Actual / Expected) )
        psi = 0.0
        eps = 1e-5
        for cat, expected in self.baseline_priors.items():
            actual = observed_priors.get(cat, 0.0)
            actual_adj = max(actual, eps)
            expected_adj = max(expected, eps)
            component = (actual_adj - expected_adj) * math.log(actual_adj / expected_adj)
            psi += component

        psi_score = round(max(0.0, psi), 4)

        if psi_score < 0.10:
            status = "STABLE"
            rec = "Model distribution is well-aligned with training baselines. No retraining needed."
        elif psi_score <= 0.25:
            status = "MODERATE_DRIFT"
            rec = "Moderate distribution drift detected. Monitor subsequent telemetry and review new command patterns."
        else:
            status = "SIGNIFICANT_DRIFT"
            rec = "Critical concept drift detected (PSI > 0.25). Model retraining with recent honeypot logs recommended."

        mean_entropy = round(sum(self._entropy_window) / len(self._entropy_window), 3) if self._entropy_window else 0.0
        novelty_rate = round(sum(1 for v in self._novelty_window if v) / len(self._novelty_window), 3) if self._novelty_window else 0.0

        return DriftReport(
            window_size=n,
            psi_score=psi_score,
            drift_status=status,
            mean_prediction_entropy=mean_entropy,
            novelty_rate=novelty_rate,
            observed_distribution={k: round(v, 4) for k, v in observed_priors.items()},
            baseline_distribution={k: round(v, 4) for k, v in self.baseline_priors.items()},
            recommendation=rec,
        )


# Global singleton
drift_monitor = ConceptDriftMonitor()
