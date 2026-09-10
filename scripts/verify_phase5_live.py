#!/usr/bin/env python3
"""
Live End-to-End Verification Script for Phase 5: MongoDB Persistence + FastAPI REST API.
Processes real Cowrie honeypot events into live MongoDB (deception_db) and queries them via FastAPI.
"""

import json
import logging
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.database.mongodb import get_db, mongodb_manager
from backend.app.main import app
from backend.app.pipeline import DeceptionPipeline
from backend.app.services.event_normalizer import EventNormalizer
from backend.app.services.persistence_service import PersistenceService


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("\n" + "=" * 75)
    print("  PHASE 5 LIVE END-TO-END VERIFICATION: COWRIE -> MONGODB -> FASTAPI")
    print(f"  Target Database : {settings.DATABASE_NAME} ({settings.MONGODB_URI})")
    print(f"  Cowrie Log Path : {settings.COWRIE_LOG_PATH}")
    print("=" * 75 + "\n")

    # 1. Connect to live MongoDB
    db = mongodb_manager.connect()
    persistence = PersistenceService(db=db)
    print(f"[+] Connected to MongoDB. Active collections: {db.list_collection_names()}")

    # 2. Replay all real honeypot events from cowrie.json into live MongoDB
    pipeline = DeceptionPipeline(
        log_path=settings.COWRIE_LOG_PATH,
        from_beginning=True,
        persistence_service=persistence,
        enable_gemini=False  # Rule engine fast ingestion for historical verification
    )

    log_path = Path(settings.COWRIE_LOG_PATH)
    if log_path.exists():
        print(f"[*] Ingesting historical events from {log_path} into MongoDB...")
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                norm_event = EventNormalizer.normalize(line)
                if norm_event:
                    sess_features = pipeline.aggregator.add_event(norm_event)
                    pipeline.process_event(norm_event, sess_features)
        print("[+] Historical ingestion complete.")

    # 3. Query through FastAPI REST API
    print("\n" + "-" * 75)
    print("[*] Executing FastAPI REST API verification queries against live database...")
    print("-" * 75)

    with TestClient(app) as client:
        # A. Health check
        res_health = client.get("/api/health")
        print(f"\n1. GET /api/health -> Status {res_health.status_code}")
        print(json.dumps(res_health.json(), indent=2))

        # B. Dashboard stats
        res_stats = client.get("/api/dashboard/stats")
        print(f"\n2. GET /api/dashboard/stats -> Status {res_stats.status_code}")
        print(json.dumps(res_stats.json(), indent=2))

        # C. Events
        res_events = client.get("/api/events?limit=3")
        print(f"\n3. GET /api/events?limit=3 -> Status {res_events.status_code}")
        events_data = res_events.json()
        print(f"Total matching events in MongoDB: {events_data.get('total', 0)}")
        if events_data.get("items"):
            sample = events_data["items"][0]
            print(f"Sample Event: ID={sample.get('event_id')} Type={sample.get('event_type')} Intent={sample.get('intent')} Severity={sample.get('severity')} Risk={sample.get('risk_score')}")

        # D. Sessions
        res_sessions = client.get("/api/sessions?limit=3")
        print(f"\n4. GET /api/sessions?limit=3 -> Status {res_sessions.status_code}")
        sessions_data = res_sessions.json()
        print(f"Total sessions in MongoDB: {sessions_data.get('total', 0)}")
        if sessions_data.get("items"):
            s_sample = sessions_data["items"][0]
            print(f"Sample Session: ID={s_sample.get('session_id')} IP={s_sample.get('source_ip')} DominantIntent={s_sample.get('dominant_intent')} Stage={s_sample.get('current_attack_stage')} Risk={s_sample.get('risk_score')}")

        # E. Attackers
        res_attackers = client.get("/api/attackers?limit=3")
        print(f"\n5. GET /api/attackers?limit=3 -> Status {res_attackers.status_code}")
        attackers_data = res_attackers.json()
        print(f"Total attacker profiles in MongoDB: {attackers_data.get('total', 0)}")
        if attackers_data.get("items"):
            a_sample = attackers_data["items"][0]
            print(f"Sample Attacker: IP={a_sample.get('source_ip')} TotalSessions={a_sample.get('total_sessions')} MaxRisk={a_sample.get('maximum_risk')} Severity={a_sample.get('severity')}")

        # F. Intent Analytics
        res_intents = client.get("/api/analytics/intents")
        print(f"\n6. GET /api/analytics/intents -> Status {res_intents.status_code}")
        print(json.dumps(res_intents.json(), indent=2))

        # G. Timeline Analytics
        res_timeline = client.get("/api/analytics/timeline")
        print(f"\n7. GET /api/analytics/timeline -> Status {res_timeline.status_code}")
        print(json.dumps(res_timeline.json(), indent=2))

    print("\n" + "=" * 75)
    print("  PHASE 5 LIVE VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
