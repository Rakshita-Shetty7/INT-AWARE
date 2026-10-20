"""
Persistence Service for MongoDB.
Handles decoupled database operations for events, sessions, attackers, alerts, and analytics.
"""

from datetime import datetime, timezone
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple
from pymongo import DESCENDING
from pymongo.database import Database

from backend.app.config import settings
from backend.app.database.mongodb import get_db
from backend.app.models.database import (
    AlertDoc,
    AttackerProfileDoc,
    StoredEventDoc,
    StoredSessionDoc,
)
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import HybridClassification
from backend.app.models.risk import RiskAssessment, RiskSeverity
from backend.app.models.session_intelligence import SessionIntelligence
from backend.app.services.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class PersistenceService:
    """
    Decoupled database repository providing CRUD, profiling, and aggregation analytics for the system.
    """

    def __init__(self, db: Optional[Database] = None):
        self._db_override = db

    @property
    def db(self) -> Database:
        """
        Returns the active MongoDB database.
        """
        if self._db_override is not None:
            return self._db_override
        return get_db()

    # -------------------------------------------------------------------------
    # Event Persistence
    # -------------------------------------------------------------------------

    def save_event(
        self,
        event: NormalizedEvent,
        classification: HybridClassification,
        risk: RiskAssessment,
        behavioral_features: Optional[Dict[str, Any]] = None
    ) -> StoredEventDoc:
        """
        Saves a fully analyzed event into the 'events' collection.

        Note: alerts are intentionally NOT raised here. Alerting is driven by the
        SESSION-level cumulative risk score in update_session(), not by the
        event-level score, which is bounded below the alert threshold by design.
        """
        # Sanitize raw_event to ensure no plain passwords are stored
        sanitized_raw = dict(event.raw_event)
        if "password" in sanitized_raw:
            sanitized_raw["password"] = "[REDACTED]"

        event_doc = StoredEventDoc(
            event_id=event.event_id,
            timestamp=event.timestamp,
            session_id=event.session_id,
            source_ip=event.source_ip,
            source_port=event.source_port,
            protocol=event.protocol,
            username=event.username,
            event_type=event.event_type,
            command=event.command,
            behavioral_features=behavioral_features or {},
            intent=classification.intent,
            attack_stage=classification.attack_stage,
            confidence=classification.confidence,
            classification_source=classification.source,
            rule_evidence=classification.rule_evidence,
            ml_intent=classification.ml_intent,
            ml_confidence=classification.ml_confidence,
            ml_model_name=classification.ml_model_name,
            ml_evidence=classification.ml_evidence,
            ai_reason=classification.ai_reason,
            ai_evidence=classification.ai_evidence,
            uncertainty_score=classification.uncertainty_score,
            is_novel=classification.is_novel,
            should_abstain=classification.should_abstain,
            risk_score=risk.risk_score,
            severity=risk.severity,
            raw_event=sanitized_raw,
            created_at=datetime.now(timezone.utc)
        )

        doc_dict = event_doc.model_dump()
        self.db["events"].update_one(
            {"event_id": event.event_id},
            {"$set": doc_dict},
            upsert=True
        )

        return event_doc

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single event by event_id.
        """
        doc = self.db["events"].find_one({"event_id": event_id}, {"_id": 0})
        return doc

    def get_events(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Queries paginated events with optional filtering.
        """
        query: Dict[str, Any] = {}
        if filters:
            if filters.get("session_id"):
                query["session_id"] = filters["session_id"]
            if filters.get("source_ip"):
                query["source_ip"] = filters["source_ip"]
            if filters.get("intent"):
                query["intent"] = filters["intent"]
            if filters.get("severity"):
                query["severity"] = filters["severity"]
            if filters.get("start_time") or filters.get("end_time"):
                ts_query: Dict[str, Any] = {}
                if filters.get("start_time"):
                    ts_query["$gte"] = filters["start_time"]
                if filters.get("end_time"):
                    ts_query["$lte"] = filters["end_time"]
                query["timestamp"] = ts_query

        total = self.db["events"].count_documents(query)
        cursor = (
            self.db["events"]
            .find(query, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieves the latest N events for live dashboard streaming.
        """
        cursor = (
            self.db["events"]
            .find({}, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        return list(cursor)

    # -------------------------------------------------------------------------
    # Session Persistence
    # -------------------------------------------------------------------------

    def update_session(
        self,
        session_intelligence: SessionIntelligence,
        session_features: Optional[SessionFeatures] = None
    ) -> StoredSessionDoc:
        """
        Incrementally updates the persistent session record in MongoDB.
        """
        first_seen = session_features.first_seen if session_features and session_features.first_seen else datetime.now(timezone.utc)
        last_seen = session_features.last_seen if session_features and session_features.last_seen else datetime.now(timezone.utc)
        duration = session_features.duration_seconds if session_features else 0.0
        total_events = session_features.total_events if session_features else 1
        command_count = session_features.command_count if session_features else 0
        unique_commands = session_features.unique_commands if session_features else []
        unique_command_count = len(unique_commands)
        login_attempt_count = session_features.login_attempt_count if session_features else 0
        is_closed = session_features.is_closed if session_features else False
        protocol = session_features.protocol if session_features else "ssh"
        username = session_features.username if session_features else None

        session_doc = StoredSessionDoc(
            session_id=session_intelligence.session_id,
            source_ip=session_intelligence.source_ip,
            protocol=protocol,
            username=username,
            first_seen=first_seen,
            last_seen=last_seen,
            duration=duration,
            total_events=total_events,
            command_count=command_count,
            unique_command_count=unique_command_count,
            unique_commands=unique_commands,
            login_attempt_count=login_attempt_count,
            intent_sequence=[str(i) for i in session_intelligence.intent_sequence],
            stage_sequence=[str(s) for s in session_intelligence.stage_sequence],
            dominant_intent=session_intelligence.dominant_intent,
            current_attack_stage=session_intelligence.current_attack_stage,
            risk_score=session_intelligence.risk_score,
            severity=session_intelligence.severity,
            confidence=session_intelligence.confidence,
            key_evidence=session_intelligence.key_evidence,
            is_closed=is_closed,
            updated_at=datetime.now(timezone.utc)
        )

        doc_dict = session_doc.model_dump()
        self.db["sessions"].update_one(
            {"session_id": session_intelligence.session_id},
            {"$set": doc_dict},
            upsert=True
        )

        # Raise/escalate a security alert when the SESSION's cumulative risk crosses
        # the configured threshold. This is the ONLY alert trigger in the system;
        # event-level risk never fires alerts (it is bounded below the threshold).
        if session_intelligence.risk_score >= settings.ALERT_RISK_THRESHOLD:
            self.create_alert(
                session_id=session_intelligence.session_id,
                source_ip=session_intelligence.source_ip,
                timestamp=last_seen,
                severity=session_intelligence.severity,
                risk_score=session_intelligence.risk_score,
                intent=session_intelligence.dominant_intent,
                attack_stage=session_intelligence.current_attack_stage,
                reason=(
                    f"Session cumulative risk {session_intelligence.risk_score} "
                    f"({session_intelligence.severity}): {session_intelligence.dominant_intent} "
                    f"at stage {session_intelligence.current_attack_stage}"
                ),
            )

        # Update associated attacker profile
        if session_intelligence.source_ip:
            self.update_attacker(session_intelligence.source_ip)

        return session_doc

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single session profile.
        """
        doc = self.db["sessions"].find_one({"session_id": session_id}, {"_id": 0})
        return doc

    def get_sessions(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Queries paginated sessions with optional filtering.
        """
        query: Dict[str, Any] = {}
        if filters:
            if filters.get("source_ip"):
                query["source_ip"] = filters["source_ip"]
            if filters.get("severity"):
                query["severity"] = filters["severity"]
            if filters.get("intent"):
                query["dominant_intent"] = filters["intent"]

        total = self.db["sessions"].count_documents(query)
        cursor = (
            self.db["sessions"]
            .find(query, {"_id": 0})
            .sort("last_seen", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    # -------------------------------------------------------------------------
    # Attacker Profile Persistence
    # -------------------------------------------------------------------------

    def update_attacker(self, source_ip: str) -> Optional[AttackerProfileDoc]:
        """
        Recalculates and persists aggregated intelligence for an attacker IP.
        """
        # Aggregate server-side (single grouped query) instead of materializing every
        # session document in Python — this scales as an IP accumulates many sessions.
        grouped = list(self.db["sessions"].aggregate([
            {"$match": {"source_ip": source_ip}},
            {"$group": {
                "_id": "$source_ip",
                "total_sessions": {"$sum": 1},
                "total_events": {"$sum": "$total_events"},
                "average_risk": {"$avg": "$risk_score"},
                "maximum_risk": {"$max": "$risk_score"},
                "first_seen": {"$min": "$first_seen"},
                "last_seen": {"$max": "$last_seen"},
            }},
        ]))
        if not grouped:
            return None

        stats = grouped[0]
        total_sessions = stats.get("total_sessions", 0)
        total_events = stats.get("total_events", 0) or 0
        maximum_risk = int(stats.get("maximum_risk") or 0)
        average_risk = round(stats.get("average_risk") or 0.0, 1)
        now = datetime.now(timezone.utc)
        first_seen = stats.get("first_seen") or now
        last_seen = stats.get("last_seen") or now

        # Most recent session drives the current dominant intent & stage.
        latest = list(
            self.db["sessions"]
            .find({"source_ip": source_ip})
            .sort("last_seen", DESCENDING)
            .limit(1)
        )
        latest_session = latest[0] if latest else {}
        dominant_intent = latest_session.get("dominant_intent", "OTHER")
        current_stage = latest_session.get("current_attack_stage", "UNKNOWN")
        severity = RiskEngine.map_severity(maximum_risk)

        attacker_doc = AttackerProfileDoc(
            source_ip=source_ip,
            first_seen=first_seen,
            last_seen=last_seen,
            total_sessions=total_sessions,
            total_events=total_events,
            average_risk=average_risk,
            maximum_risk=maximum_risk,
            dominant_intent=dominant_intent,
            current_stage=current_stage,
            severity=severity,
            updated_at=datetime.now(timezone.utc)
        )

        doc_dict = attacker_doc.model_dump()
        self.db["attackers"].update_one(
            {"source_ip": source_ip},
            {"$set": doc_dict},
            upsert=True
        )
        return attacker_doc

    def get_attacker(self, source_ip: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves attacker host profile by IP.
        """
        return self.db["attackers"].find_one({"source_ip": source_ip}, {"_id": 0})

    def get_attackers(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Queries paginated attacker profiles.
        """
        query: Dict[str, Any] = {}
        if filters and filters.get("source_ip"):
            query["source_ip"] = filters["source_ip"]

        total = self.db["attackers"].count_documents(query)
        cursor = (
            self.db["attackers"]
            .find(query, {"_id": 0})
            .sort("maximum_risk", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    # -------------------------------------------------------------------------
    # Alerts Persistence
    # -------------------------------------------------------------------------

    @staticmethod
    def alert_id_for_session(session_id: str) -> str:
        """
        Deterministic, session-scoped alert identifier.

        One alert per session: the alert escalates in place as the session's
        cumulative risk grows, instead of spamming one row per event. Shared by
        the persistence layer and the WebSocket broadcaster so both reference the
        exact same alert_id.
        """
        return "ALT-" + hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:12]

    def create_alert(
        self,
        session_id: str,
        source_ip: Optional[str],
        timestamp: datetime,
        severity: RiskSeverity,
        risk_score: int,
        intent: Any,
        attack_stage: Any,
        reason: str
    ) -> AlertDoc:
        """
        Creates or escalates the session's security alert.

        Keyed on session_id (one alert per session): the first threshold crossing
        inserts the alert; later crossings update the risk score, severity, stage,
        and reason in place while preserving the original detection time
        (created_at) and any analyst-set status.
        """
        alert_id = self.alert_id_for_session(session_id)

        alert_doc = AlertDoc(
            alert_id=alert_id,
            session_id=session_id,
            source_ip=source_ip,
            timestamp=timestamp,
            severity=severity,
            risk_score=risk_score,
            intent=intent,
            attack_stage=attack_stage,
            reason=reason,
            status="OPEN",
            created_at=datetime.now(timezone.utc)
        )

        doc_dict = alert_doc.model_dump()
        # created_at and status are written only on first insert so the original
        # detection time and analyst triage state survive later escalations.
        set_on_insert = {
            "created_at": doc_dict.pop("created_at"),
            "status": doc_dict.pop("status"),
        }
        self.db["alerts"].update_one(
            {"alert_id": alert_id},
            {"$set": doc_dict, "$setOnInsert": set_on_insert},
            upsert=True
        )
        logger.info(
            "[ALERT] alert_id=%s session=%s score=%s severity=%s",
            alert_id, session_id, risk_score, severity
        )
        return alert_doc

    def get_alerts(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Queries paginated alerts.
        """
        query: Dict[str, Any] = {}
        if filters:
            if filters.get("status"):
                query["status"] = filters["status"]
            if filters.get("severity"):
                query["severity"] = filters["severity"]
            if filters.get("session_id"):
                query["session_id"] = filters["session_id"]

        total = self.db["alerts"].count_documents(query)
        cursor = (
            self.db["alerts"]
            .find(query, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    # -------------------------------------------------------------------------
    # Executive Analytics & Dashboard Aggregations
    # -------------------------------------------------------------------------

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Aggregates system-wide summary metrics for the executive dashboard.
        """
        total_sessions = self.db["sessions"].count_documents({})
        active_sessions = self.db["sessions"].count_documents({"is_closed": False})
        total_events = self.db["events"].count_documents({})
        total_attackers = self.db["attackers"].count_documents({})
        high_risk_sessions = self.db["sessions"].count_documents({"severity": "HIGH"})
        critical_sessions = self.db["sessions"].count_documents({"severity": "CRITICAL"})
        open_alerts = self.db["alerts"].count_documents({"status": "OPEN"})

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_events": total_events,
            "total_attackers": total_attackers,
            "high_risk_sessions": high_risk_sessions,
            "critical_sessions": critical_sessions,
            "open_alerts": open_alerts
        }

    def get_intent_analytics(self) -> List[Dict[str, Any]]:
        """
        Calculates percentage distribution of classified attacker intents.
        """
        total_events = self.db["events"].count_documents({})
        if total_events == 0:
            return []

        pipeline = [
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        results = list(self.db["events"].aggregate(pipeline))

        analytics = []
        for r in results:
            count = r["count"]
            pct = round((count / total_events) * 100, 1)
            analytics.append({
                "intent": r["_id"] or "OTHER",
                "count": count,
                "percentage": pct
            })
        return analytics

    def get_severity_analytics(self) -> List[Dict[str, Any]]:
        """
        Calculates severity distribution across all sessions.
        """
        total_sessions = self.db["sessions"].count_documents({})
        if total_sessions == 0:
            return []

        pipeline = [
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        results = list(self.db["sessions"].aggregate(pipeline))

        analytics = []
        for r in results:
            count = r["count"]
            pct = round((count / total_sessions) * 100, 1)
            analytics.append({
                "severity": r["_id"] or "LOW",
                "count": count,
                "percentage": pct
            })
        return analytics

    def get_timeline_analytics(self) -> List[Dict[str, Any]]:
        """
        Groups event and session telemetry into chronological time buckets for charting.
        """
        pipeline = [
            {
                "$project": {
                    "bucket": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:00:00Z",
                            "date": "$timestamp"
                        }
                    },
                    "session_id": 1,
                    "risk_score": 1
                }
            },
            {
                "$group": {
                    "_id": "$bucket",
                    "event_count": {"$sum": 1},
                    "sessions": {"$addToSet": "$session_id"},
                    "max_risk": {"$max": "$risk_score"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        results = list(self.db["events"].aggregate(pipeline))

        timeline = []
        for r in results:
            timeline.append({
                "timestamp": r["_id"],
                "event_count": r["event_count"],
                "session_count": len(r.get("sessions", [])),
                "max_risk": r.get("max_risk", 0)
            })
        return timeline

    def get_stage_analytics(self) -> List[Dict[str, Any]]:
        """
        Calculates distribution of attack stages reached across sessions.
        """
        total_sessions = self.db["sessions"].count_documents({})
        if total_sessions == 0:
            return []

        pipeline = [
            {"$group": {"_id": "$current_attack_stage", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        results = list(self.db["sessions"].aggregate(pipeline))

        analytics = []
        for r in results:
            count = r["count"]
            pct = round((count / total_sessions) * 100, 1)
            analytics.append({
                "stage": r["_id"] or "UNKNOWN",
                "count": count,
                "percentage": pct
            })
        return analytics

    def get_risk_distribution(self) -> List[Dict[str, Any]]:
        """
        Calculates session distribution across 4 standardized threat risk buckets.
        Always returns all 4 buckets (zero-filled when empty) so the dashboard chart
        renders a stable set of categories.
        """
        total_sessions = self.db["sessions"].count_documents({})
        low = self.db["sessions"].count_documents({"risk_score": {"$lt": 25}})
        medium = self.db["sessions"].count_documents({"risk_score": {"$gte": 25, "$lt": 50}})
        high = self.db["sessions"].count_documents({"risk_score": {"$gte": 50, "$lt": 75}})
        critical = self.db["sessions"].count_documents({"risk_score": {"$gte": 75}})

        def _pct(n: int) -> float:
            return round((n / total_sessions) * 100, 1) if total_sessions else 0.0

        buckets = [
            {"range": "0-24 (Low)", "count": low, "percentage": _pct(low)},
            {"range": "25-49 (Medium)", "count": medium, "percentage": _pct(medium)},
            {"range": "50-74 (High)", "count": high, "percentage": _pct(high)},
            {"range": "75-100 (Critical)", "count": critical, "percentage": _pct(critical)},
        ]
        return buckets

    def get_risk_intent_heatmap(self) -> List[Dict[str, Any]]:
        """
        Calculates a cross-dimensional Intent x Risk/Severity heatmap.
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$intent",
                    "event_count": {"$sum": 1},
                    "avg_risk": {"$avg": "$risk_score"},
                    "max_risk": {"$max": "$risk_score"},
                    "low_count": {"$sum": {"$cond": [{"$eq": ["$severity", "LOW"]}, 1, 0]}},
                    "med_count": {"$sum": {"$cond": [{"$eq": ["$severity", "MEDIUM"]}, 1, 0]}},
                    "high_count": {"$sum": {"$cond": [{"$eq": ["$severity", "HIGH"]}, 1, 0]}},
                    "crit_count": {"$sum": {"$cond": [{"$eq": ["$severity", "CRITICAL"]}, 1, 0]}}
                }
            },
            {"$sort": {"avg_risk": -1}}
        ]
        results = list(self.db["events"].aggregate(pipeline))

        heatmap = []
        for r in results:
            heatmap.append({
                "intent": r["_id"] or "OTHER",
                "event_count": r["event_count"],
                "average_risk": round(r.get("avg_risk", 0), 1),
                "max_risk": r.get("max_risk", 0),
                "low": r.get("low_count", 0),
                "medium": r.get("med_count", 0),
                "high": r.get("high_count", 0),
                "critical": r.get("crit_count", 0)
            })
        return heatmap
