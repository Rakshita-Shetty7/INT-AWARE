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
from backend.app.services.feature_extractor import FeatureExtractor
from backend.app.services.gemini_classifier import GeminiClassifier
from backend.app.services.hybrid_classifier import HybridClassifier
from backend.app.services.log_collector import AsyncLogCollector
from backend.app.services.persistence_service import PersistenceService
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.rule_classifier import RuleClassifier
from backend.app.services.session_aggregator import SessionAggregator
from backend.app.services.session_intelligence import SessionIntelligenceEngine

logger = logging.getLogger(__name__)


class DeceptionPipeline:
    """
    Orchestrates real-time telemetry streaming from Cowrie JSON into classification,
    risk assessment, and MongoDB persistence.
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

            # 5. Persist to MongoDB (with error resilience)
            try:
                # Save analyzed event record
                self.persistence.save_event(
                    event=event,
                    classification=classification,
                    risk=risk,
                    behavioral_features=event_features.model_dump()
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
                    "risk_score": risk.risk_score,
                    "severity": str(risk.severity),
                }
                websocket_manager.broadcast_event(ws_event_payload)

                if risk.risk_score >= 75:
                    ws_alert_payload = {
                        "type": "alert",
                        "alert_id": f"ALT-{event.event_id[:8]}",
                        "session_id": event.session_id,
                        "source_ip": event.source_ip,
                        "intent": str(classification.intent),
                        "attack_stage": str(classification.attack_stage),
                        "risk_score": risk.risk_score,
                        "severity": str(risk.severity),
                        "reason": f"High risk threat detected: {classification.intent} ({classification.attack_stage})",
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
