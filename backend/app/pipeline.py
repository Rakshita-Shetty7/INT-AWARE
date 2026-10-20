"""
Integrated Honeypot Processing & Persistence Pipeline.
Connects AsyncLogCollector to Normalizer, FeatureExtractor, HybridClassifier, RiskEngine,
SessionIntelligence, and PersistenceService (MongoDB).
"""

import asyncio
import logging
from typing import Optional

from backend.app.config import settings
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.services.adaptive_deception_engine import AdaptiveDeceptionEngine
from backend.app.services.feature_extractor import FeatureExtractor
from backend.app.services.gemini_classifier import GeminiClassifier
from backend.app.services.hybrid_classifier import HybridClassifier
from backend.app.services.log_collector import AsyncLogCollector
from backend.app.services.persistence_service import PersistenceService
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.rule_classifier import RuleClassifier
from backend.app.services.sequence_transition_engine import SequenceTransitionEngine
from backend.app.services.session_aggregator import SessionAggregator
from backend.app.services.session_intelligence import SessionIntelligenceEngine

logger = logging.getLogger(__name__)


class DeceptionPipeline:
    """
    Orchestrates real-time telemetry streaming from Cowrie JSON into classification,
    risk assessment, Markov sequence transition modeling, adaptive deception, and MongoDB persistence.
    """

    def __init__(
        self,
        log_path: Optional[str] = None,
        from_beginning: bool = False,
        persistence_service: Optional[PersistenceService] = None,
        enable_gemini: bool = True
    ):
        self.log_path = log_path or settings.COWRIE_LOG_PATH
        self.from_beginning = from_beginning
        self.persistence = persistence_service or PersistenceService()

        # Component instances
        self.aggregator = SessionAggregator()
        self.rule_classifier = RuleClassifier()
        self.gemini_classifier = GeminiClassifier(enabled=enable_gemini)
        self.hybrid_classifier = HybridClassifier(
            rule_classifier=self.rule_classifier,
            gemini_classifier=self.gemini_classifier
        )
        self.risk_engine = RiskEngine()
        self.session_intelligence_engine = SessionIntelligenceEngine()
        self.sequence_engine = SequenceTransitionEngine()
        self.deception_engine = AdaptiveDeceptionEngine()

        # Collector instance
        self.collector = AsyncLogCollector(
            log_path=self.log_path,
            aggregator=self.aggregator,
            from_beginning=self.from_beginning
        )
        self.collector.register_callback(self.process_event)

    def process_event(self, event: NormalizedEvent, session_features: SessionFeatures) -> None:
        """
        Callback executed synchronously for each newly ingested and normalized event.
        """
        try:
            # 1. Extract granular event features
            event_features = FeatureExtractor.extract_event_features(event)

            # 2. Hybrid Intent & Attack Stage Classification
            classification = self.hybrid_classifier.classify(event, session_features)

            # 3. Deterministic Threat Risk Evaluation
            risk = self.risk_engine.evaluate(event, classification, session_features)

            # 4. Update Session Intelligence Attacker Profile
            session_intelligence = self.session_intelligence_engine.update_session(
                event=event,
                classification=classification,
                session_features=session_features
            )

            # 4b. Markov Sequence Transition Analysis & Next-Intent Projection
            prior_intents = session_intelligence.intent_sequence[:-1] if session_intelligence.intent_sequence else []
            transition_analysis = self.sequence_engine.evaluate_transition(
                current_intent=classification.intent,
                intent_history=prior_intents,
                inter_command_delays=getattr(session_features, "command_intervals", []),
            )

            # 4b-2. Record distribution telemetry into Concept Drift Monitor
            try:
                from backend.app.ml.drift_monitor import drift_monitor
                drift_monitor.record_prediction(
                    intent=str(classification.intent),
                    entropy=getattr(classification, "uncertainty_score", 0.0),
                    is_novel=getattr(classification, "is_novel", False),
                )
            except Exception as d_err:
                logger.debug("Failed recording drift metric: %s", d_err)

            # 4c. Safe Adaptive Deception Response Generation (Zero Host Execution)
            deception_decision = self.deception_engine.select_deception_response(
                command=event.command,
                intent=classification.intent,
                attack_stage=classification.attack_stage,
                session_id=event.session_id,
                risk_score=risk.risk_score,
            )

            # Enrich event features with sequence intelligence and deception metadata
            behavioral_dict = event_features.model_dump()
            behavioral_dict["sequence_anomaly_score"] = transition_analysis.sequence_anomaly_score
            behavioral_dict["is_anomalous_transition"] = transition_analysis.is_anomalous_transition
            behavioral_dict["progression_pace"] = transition_analysis.progression_pace
            behavioral_dict["predicted_next_intents"] = [p.model_dump() for p in transition_analysis.predicted_next_intents]
            behavioral_dict["deception_strategy"] = deception_decision.strategy.value
            behavioral_dict["deception_policy"] = deception_decision.policy_id
            behavioral_dict["deception_delay_ms"] = deception_decision.delay_ms
            behavioral_dict["honeytokens_injected"] = deception_decision.honeytokens_injected

            # 5. Persist to MongoDB (with error resilience)
            try:
                # Save analyzed event record
                self.persistence.save_event(
                    event=event,
                    classification=classification,
                    risk=risk,
                    behavioral_features=behavioral_dict
                )

                # Update persistent session document
                self.persistence.update_session(
                    session_intelligence=session_intelligence,
                    session_features=session_features
                )
            except Exception as db_err:
                logger.error("MongoDB persistence failed for event %s: %s", event.event_id, db_err)

            # 6. Broadcast real-time WebSocket telemetry to connected dashboard clients
            try:
                from backend.app.services.websocket_manager import websocket_manager

                ws_event_payload = {
                    "type": "event",
                    "event_id": event.event_id,
                    "session_id": event.session_id,
                    "timestamp": event.timestamp.isoformat(),
                    "source_ip": event.source_ip,
                    "username": event.username,
                    "event_type": event.event_type,
                    "command": event.command,
                    "intent": str(classification.intent),
                    "attack_stage": str(classification.attack_stage),
                    "confidence": classification.confidence,
                    "classification_source": str(classification.source),
                    "ml_intent": str(classification.ml_intent) if classification.ml_intent else None,
                    "ml_confidence": classification.ml_confidence,
                    "ml_model_name": classification.ml_model_name,
                    "uncertainty_score": classification.uncertainty_score,
                    "is_novel": classification.is_novel,
                    "should_abstain": classification.should_abstain,
                    "sequence_anomaly_score": transition_analysis.sequence_anomaly_score,
                    "predicted_next_intents": [p.model_dump() for p in transition_analysis.predicted_next_intents],
                    "deception_strategy": deception_decision.strategy.value,
                    "deception_policy": deception_decision.policy_id,
                    "deception_delay_ms": deception_decision.delay_ms,
                    "risk_score": risk.risk_score,
                    "severity": str(risk.severity),
                }
                websocket_manager.broadcast_event(ws_event_payload)

                # Alerts are driven by the SESSION cumulative risk (reaches 100),
                # never by the event-level score (bounded below the threshold).
                # alert_id matches the persisted alert so the dashboard updates one
                # card per session instead of stacking a new card per event.
                if session_intelligence.risk_score >= settings.ALERT_RISK_THRESHOLD:
                    ws_alert_payload = {
                        "type": "alert",
                        "alert_id": self.persistence.alert_id_for_session(event.session_id),
                        "session_id": event.session_id,
                        "source_ip": event.source_ip,
                        "intent": str(session_intelligence.dominant_intent),
                        "attack_stage": str(session_intelligence.current_attack_stage),
                        "risk_score": session_intelligence.risk_score,
                        "severity": str(session_intelligence.severity),
                        "reason": (
                            f"Session cumulative risk {session_intelligence.risk_score} "
                            f"({session_intelligence.severity}): {session_intelligence.dominant_intent} "
                            f"at stage {session_intelligence.current_attack_stage}"
                        ),
                        "status": "OPEN",
                        "timestamp": event.timestamp.isoformat(),
                    }
                    websocket_manager.broadcast_alert(ws_alert_payload)

            except Exception as ws_err:
                logger.debug("[WS] WebSocket broadcast failed: %s", ws_err)

        except Exception as err:
            logger.error("Unexpected error in pipeline processing event %s: %s", event.event_id, err, exc_info=True)

    async def start(self) -> None:
        """
        Starts the asynchronous log collector loop.
        """
        logger.info("Starting DeceptionPipeline on %s (from_beginning=%s)", self.log_path, self.from_beginning)
        await self.collector.start()

    def stop(self) -> None:
        """
        Stops the pipeline gracefully.
        """
        logger.info("Stopping DeceptionPipeline...")
        self.collector.stop()
