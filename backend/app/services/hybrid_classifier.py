"""
Hybrid Intent Classifier Service.

Arbitrates between three complementary sources of intelligence and consolidates
their evidence into a single, explainable decision:

  1. Rule Engine  — deterministic, high-precision signatures for known-malicious
                    command patterns (authoritative when a strong signature fires).
  2. ML model     — a trained command->intent classifier that generalises across
                    command variants and provides a calibrated confidence.
  3. Gemini LLM   — a semantic reasoner consulted ONLY for genuinely ambiguous
                    cases (weak rule + low-confidence ML). Entirely optional:
                    the system runs fully without it.

Decision precedence:
    strong rule signature  >  confident ML  >  Gemini  >  best-available  >  OTHER
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.app.config import settings
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import (
    AttackStage,
    ClassificationSource,
    HybridClassification,
    IntentCategory,
)
from backend.app.ml.intent_ml_classifier import MLIntentClassifier, ml_intent_classifier
from backend.app.services.gemini_classifier import GeminiClassifier
from backend.app.services.rule_classifier import RuleClassifier

logger = logging.getLogger(__name__)


class HybridClassifier:
    """
    Hybrid classification engine coordinating deterministic rules, a trained ML
    model, and optional LLM contextual reasoning.
    """

    def __init__(
        self,
        rule_classifier: Optional[RuleClassifier] = None,
        gemini_classifier: Optional[GeminiClassifier] = None,
        ml_classifier: Optional[MLIntentClassifier] = None,
        rule_confidence_threshold: float = 0.90,
        ml_confidence_threshold: float = 0.40,
    ):
        self.rule_classifier = rule_classifier or RuleClassifier()
        self.gemini_classifier = gemini_classifier or GeminiClassifier()
        # Falls back to the module singleton; if the artifact is missing it simply
        # reports available == False and the ML branch is skipped.
        self.ml_classifier = ml_classifier if ml_classifier is not None else ml_intent_classifier
        self.rule_confidence_threshold = rule_confidence_threshold
        self.ml_confidence_threshold = ml_confidence_threshold

    def classify(
        self,
        event: NormalizedEvent,
        session_features: Optional[SessionFeatures] = None,
    ) -> HybridClassification:
        """
        Classifies an incoming event using the hybrid decision arbitration pipeline.
        """
        has_command = event.command is not None and len(event.command.strip()) > 0

        # ---- Gather source opinions ------------------------------------- #
        rule_result = None
        if settings.RULE_ENGINE_ENABLED:
            rule_result = self.rule_classifier.classify(event, session_features)

        ml_result = None
        if has_command and self.ml_classifier is not None and self.ml_classifier.available:
            ml_result = self.ml_classifier.classify(event.command)

        strong_rule = (
            rule_result is not None
            and bool(rule_result.rule_matches)
            and rule_result.confidence >= self.rule_confidence_threshold
            and rule_result.intent != IntentCategory.OTHER
        )
        ml_confident = ml_result is not None and ml_result.confidence >= self.ml_confidence_threshold

        # Consult Gemini only when neither rule nor ML is decisive (keeps it optional).
        should_query_gemini = (
            self.gemini_classifier.enabled
            and has_command
            and not strong_rule
            and not ml_confident
        )
        ai_result = (
            self.gemini_classifier.classify(event, session_features)
            if should_query_gemini else None
        )

        # ---- Arbitrate --------------------------------------------------- #
        if strong_rule:
            # High-precision known signature. ML/Gemini act as corroboration only.
            agree = ml_result is not None and ml_result.intent == rule_result.intent
            source = ClassificationSource.HYBRID if (agree or ai_result is not None) else ClassificationSource.RULE
            final_intent, final_stage, final_conf = (
                rule_result.intent, rule_result.attack_stage, rule_result.confidence)

        elif ml_confident:
            # Trained model is confident. If a rule signature agrees, it's HYBRID.
            rule_agree = (
                rule_result is not None
                and rule_result.intent == ml_result.intent
                and rule_result.intent != IntentCategory.OTHER
            )
            source = ClassificationSource.HYBRID if rule_agree else ClassificationSource.ML
            final_intent, final_stage = ml_result.intent, ml_result.attack_stage
            final_conf = max(ml_result.confidence, rule_result.confidence) if rule_agree else ml_result.confidence

        elif ai_result is not None:
            # Ambiguous case resolved by the semantic layer.
            source = (
                ClassificationSource.HYBRID
                if (rule_result is not None and rule_result.rule_matches) else ClassificationSource.GEMINI
            )
            if rule_result is not None and rule_result.confidence >= 0.85 and ai_result.confidence < 0.70:
                final_intent, final_stage, final_conf = (
                    rule_result.intent, rule_result.attack_stage, rule_result.confidence)
            else:
                final_intent, final_stage, final_conf = (
                    ai_result.intent, ai_result.attack_stage, ai_result.confidence)

        elif ml_result is not None or rule_result is not None:
            # No decisive/optional source fired: take the best available opinion.
            prefer_ml = ml_result is not None and (
                rule_result is None
                or rule_result.intent == IntentCategory.OTHER
                or ml_result.confidence >= rule_result.confidence
            )
            if prefer_ml:
                source = ClassificationSource.ML
                final_intent, final_stage, final_conf = (
                    ml_result.intent, ml_result.attack_stage, ml_result.confidence)
            else:
                source = ClassificationSource.FALLBACK if should_query_gemini else ClassificationSource.RULE
                final_intent, final_stage, final_conf = (
                    rule_result.intent, rule_result.attack_stage, rule_result.confidence)

        else:
            # Nothing available at all.
            final_intent, final_stage, final_conf = (
                IntentCategory.OTHER, AttackStage.UNKNOWN, 0.10)
            source = ClassificationSource.FALLBACK

        # Compute calibrated epistemic uncertainty and abstention criteria
        is_novel = bool(ml_result.is_novel if ml_result else False)
        if strong_rule:
            uncertainty = round(float(1.0 - final_conf), 4)
            should_abstain = False
        else:
            novelty_contrib = ml_result.novelty_score if ml_result else 0.5
            uncertainty = round(float(min(1.0, max(1.0 - final_conf, novelty_contrib))), 4)
            should_abstain = bool(is_novel or (ml_result and ml_result.should_abstain) or final_conf < 0.35)

        classification = HybridClassification(
            intent=final_intent,
            attack_stage=final_stage,
            confidence=round(final_conf, 2),
            source=source,
            rule_evidence=rule_result.evidence if rule_result else (
                [] if (ml_result or ai_result) else ["Both rule engine and ML/AI classifiers unavailable"]
            ),
            ml_intent=ml_result.intent if ml_result else None,
            ml_confidence=round(ml_result.confidence, 4) if ml_result else None,
            ml_model_name=ml_result.model_name if ml_result else None,
            ml_evidence=ml_result.evidence if ml_result else [],
            ai_reason=ai_result.reason if ai_result else None,
            ai_evidence=ai_result.evidence if ai_result else [],
            uncertainty_score=uncertainty,
            is_novel=is_novel,
            should_abstain=should_abstain,
            timestamp=datetime.now(timezone.utc),
        )

        logger.info(
            "[CLASSIFICATION] session=%s intent=%s stage=%s source=%s confidence=%.2f "
            "(ml=%s%s)",
            event.session_id,
            classification.intent,
            classification.attack_stage,
            classification.source,
            classification.confidence,
            ml_result.intent if ml_result else "n/a",
            f"@{ml_result.confidence:.2f}" if ml_result else "",
        )

        return classification
