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
        self._word_vocab: set = set()
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

                # Extract word vocabulary for out-of-vocabulary (OOV) novelty calculation
                try:
                    features_step = getattr(self._pipeline, "named_steps", {}).get("features")
                    if features_step and hasattr(features_step, "transformer_list"):
                        for name, trans in features_step.transformer_list:
                            if name == "word" and hasattr(trans, "vocabulary_") and trans.vocabulary_:
                                self._word_vocab = set(trans.vocabulary_.keys())
                except Exception as ve:
                    logger.debug("[ML] Could not cache word vocabulary for OOV scoring: %s", ve)

                self._loaded = True
                logger.info(
                    "[ML] Loaded intent classifier '%s' (%d classes, vocab=%d) from %s",
                    self._model_name, len(self._classes), len(self._word_vocab), self.model_path,
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
        Includes Shannon entropy, vocabulary novelty detection, and abstention recommendation.
        """
        if not self.available:
            return None
        if not command or not command.strip():
            return None

        import math

        cmd = command.strip()
        try:
            proba = self._pipeline.predict_proba([cmd])[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("[ML] Inference failed for command=%r: %s", cmd, exc)
            return None

        # Shannon entropy across all classes: H(p) = -sum(p * log2(p))
        entropy = -sum(float(p) * math.log2(float(p) + 1e-12) for p in proba if p > 0.0)
        max_entropy = math.log2(max(len(self._classes), 2))
        norm_entropy = min(1.0, max(0.0, entropy / max_entropy))

        # Vocabulary novelty ratio: fraction of word tokens unseen during training
        tokens = [t.lower() for t in cmd.split() if len(t) > 1]
        if tokens and self._word_vocab:
            oov_count = sum(1 for t in tokens if t not in self._word_vocab)
            oov_ratio = oov_count / len(tokens)
        else:
            oov_ratio = norm_entropy

        novelty_score = round(min(1.0, 0.6 * norm_entropy + 0.4 * oov_ratio), 4)

        # Rank classes by probability.
        ranked = sorted(zip(self._classes, proba), key=lambda t: t[1], reverse=True)
        top_intent, top_conf = ranked[0]
        top_predictions = [
            {"intent": cls, "probability": round(float(p), 4)}
            for cls, p in ranked[: self.top_k]
        ]

        is_novel = bool(novelty_score >= 0.70 or (top_conf < 0.28 and norm_entropy > 0.80))
        should_abstain = bool(is_novel or top_conf < 0.30)

        evidence = [
            f"ML model '{self._model_name}' predicted {top_intent} "
            f"with calibrated probability {top_conf:.2f}",
        ]
        if len(ranked) > 1:
            second_cls, second_p = ranked[1]
            evidence.append(f"Next most likely: {second_cls} ({second_p:.2f})")

        if is_novel:
            evidence.append(
                f"Novelty/OOD detected: entropy={entropy:.2f} bits (norm={norm_entropy:.2f}), "
                f"novelty_score={novelty_score:.2f} -> Abstention recommended"
            )

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
            entropy=round(float(entropy), 4),
            novelty_score=novelty_score,
            is_novel=is_novel,
            should_abstain=should_abstain,
        )


# Module-level singleton used by the hybrid classifier / pipeline.
ml_intent_classifier = MLIntentClassifier()
