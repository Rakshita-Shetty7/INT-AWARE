"""
Session Aggregator Service.
Maintains live, incremental session-level states and behavioral feature profiles.
"""

import logging
import threading
from typing import Dict, List, Optional

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.services.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class SessionAggregator:
    """
    In-memory state aggregator that tracks active attacker sessions and updates
    their behavioral profiles incrementally as events arrive.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._session_events: Dict[str, List[NormalizedEvent]] = {}
        self._session_features: Dict[str, SessionFeatures] = {}

    def add_event(self, event: NormalizedEvent) -> SessionFeatures:
        """
        Ingests a normalized event, adds it to the corresponding session buffer,
        and incrementally re-computes updated SessionFeatures.
        """
        with self._lock:
            session_id = event.session_id
            if session_id not in self._session_events:
                self._session_events[session_id] = []

            # Check for duplicate event within this session
            existing_ids = {e.event_id for e in self._session_events[session_id]}
            if event.event_id not in existing_ids:
                self._session_events[session_id].append(event)

            # Re-compute updated session features
            features = FeatureExtractor.compute_session_features(
                session_id=session_id,
                events=self._session_events[session_id]
            )
            self._session_features[session_id] = features
            return features

    def get_session(self, session_id: str) -> Optional[SessionFeatures]:
        """
        Retrieves the current feature state for a specific session.
        """
        with self._lock:
            return self._session_features.get(session_id)

    def get_all_sessions(self) -> Dict[str, SessionFeatures]:
        """
        Retrieves all currently tracked session feature profiles.
        """
        with self._lock:
            return dict(self._session_features)

    def get_session_events(self, session_id: str) -> List[NormalizedEvent]:
        """
        Retrieves all normalized events recorded for a given session.
        """
        with self._lock:
            return list(self._session_events.get(session_id, []))

    def clear(self) -> None:
        """
        Clears all in-memory session records (used primarily in tests).
        """
        with self._lock:
            self._session_events.clear()
            self._session_features.clear()
