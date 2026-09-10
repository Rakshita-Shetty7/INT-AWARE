"""
Runtime ML intent classifier.

Loads the trained scikit-learn pipeline (produced by ``backend.app.ml.train``)
and classifies a single command string into one of the 10 intent categories,
with a calibrated confidence and an explainable set of alternatives.

Design contract (matches the rest of the system):
  * Never raises on a bad/missing artifact — if the model cannot be loaded the
    classifier reports ``available == False`` and ``classify()`` returns ``None``.
    The hybrid classifier then simply proceeds without the ML source.
  * Pure, side-effect-free inference (no I/O beyond the one-time model load).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import List, Optional

from backend.app.models.intent import (
    AttackStage,
    IntentCategory,
    MLClassification,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "intent_classifier.joblib"


class MLIntentClassifier:
    """Thread-safe, lazily-loaded wrapper around the trained command->intent pipeline."""

    def __init__(self, model_path: Optional[Path] = None, top_k: int = 3):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.top_k = top_k
        self._pipeline = None
        self._classes: List[str] = []
        self._model_name: str = "unknown"
        self._intent_to_stage: dict = {}
        self._loaded = False
        self._load_error: Optional[str] = None
        self._lock = threading.Lock()
        self._load()

    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        """Loads the joblib artifact once; degrades gracefully on any failure."""
        with self._lock:
            if self._loaded:
                return
            try:
                import joblib  # local import so a missing dep never breaks startup

                if not self.model_path.exists():
                    raise FileNotFoundError(f"model artifact not found at {self.model_path}")

                bundle = joblib.load(self.model_path)
                self._pipeline = bundle["pipeline"]
                meta = bundle.get("metadata", {})
                self._model_name = meta.get("model_name", "ml_pipeline")
                self._intent_to_stage = meta.get("intent_to_stage", {})
                self._classes = list(getattr(self._pipeline, "classes_", []))
                self._loaded = True
                logger.info(
                    "[ML] Loaded intent classifier '%s' (%d classes) from %s",
                    self._model_name, len(self._classes), self.model_path,
                )
            except Exception as exc:  # noqa: BLE001 - defensive by design
                self._load_error = str(exc)
                self._loaded = False
                logger.warning(
                    "[ML] Intent classifier unavailable (%s). "
                    "System will run on rules%s.",
                    exc, " + Gemini" if True else "",
                )

    @property
    def available(self) -> bool:
        return self._loaded and self._pipeline is not None

    # ------------------------------------------------------------------ #
    def _stage_for(self, intent: str) -> AttackStage:
        stage = self._intent_to_stage.get(intent, "UNKNOWN")
        try:
            return AttackStage(stage)
        except ValueError:
            return AttackStage.UNKNOWN

    def classify(self, command: Optional[str]) -> Optional[MLClassification]:
        """
        Classifies a command string. Returns None when the model is unavailable
        or the input carries no command text (ML only reasons over commands).
        """
        if not self.available:
            return None
        if not command or not command.strip():
            return None

        cmd = command.strip()
        try:
            proba = self._pipeline.predict_proba([cmd])[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("[ML] Inference failed for command=%r: %s", cmd, exc)
            return None

        # Rank classes by probability.
        ranked = sorted(zip(self._classes, proba), key=lambda t: t[1], reverse=True)
        top_intent, top_conf = ranked[0]
        top_predictions = [
            {"intent": cls, "probability": round(float(p), 4)}
            for cls, p in ranked[: self.top_k]
        ]

        evidence = [
            f"ML model '{self._model_name}' predicted {top_intent} "
            f"with calibrated probability {top_conf:.2f}",
        ]
        if len(ranked) > 1:
            second_cls, second_p = ranked[1]
            evidence.append(f"Next most likely: {second_cls} ({second_p:.2f})")

        try:
            intent_enum = IntentCategory(top_intent)
        except ValueError:
            intent_enum = IntentCategory.OTHER

        return MLClassification(
            intent=intent_enum,
            attack_stage=self._stage_for(top_intent),
            confidence=round(float(top_conf), 4),
            model_name=self._model_name,
            top_predictions=top_predictions,
            evidence=evidence,
        )


# Module-level singleton used by the hybrid classifier / pipeline.
ml_intent_classifier = MLIntentClassifier()
