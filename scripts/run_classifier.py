#!/usr/bin/env python3
"""
CLI Test Runner for Phase 4: Hybrid Intent Classification & Risk Assessment Pipeline.
Processes live or historical Cowrie honeypot events and outputs full classification diagnostics.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.services.gemini_classifier import GeminiClassifier
from backend.app.services.hybrid_classifier import HybridClassifier
from backend.app.services.log_collector import AsyncLogCollector
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.rule_classifier import RuleClassifier
from backend.app.services.session_aggregator import SessionAggregator
from backend.app.services.session_intelligence import SessionIntelligenceEngine


def main():
    parser = argparse.ArgumentParser(description="Intent-Aware Deception System — Hybrid Classification CLI")
    parser.add_argument(
        "--log-path",
        default=settings.COWRIE_LOG_PATH,
        help="Path to cowrie.json log file"
    )
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        help="Process all events from beginning of cowrie.json"
    )
    parser.add_argument(
        "--no-gemini",
        action="store_true",
        help="Disable Gemini LLM classification and use rule engine only"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    aggregator = SessionAggregator()
    rule_classifier = RuleClassifier()
    gemini_classifier = GeminiClassifier(enabled=not args.no_gemini)
    hybrid_classifier = HybridClassifier(
        rule_classifier=rule_classifier,
        gemini_classifier=gemini_classifier
    )
    risk_engine = RiskEngine()
    session_intelligence_engine = SessionIntelligenceEngine()

    print("\n" + "=" * 75)
    print("  INTENT-AWARE DECEPTION SYSTEM — HYBRID CLASSIFICATION ENGINE")
    print(f"  Log Source      : {args.log_path}")
    print(f"  Replay Mode     : {'From Beginning' if args.from_beginning else 'Live Tail'}")
    print(f"  Rule Engine     : Enabled")
    print(f"  Gemini LLM      : {'Enabled (' + settings.GEMINI_MODEL + ')' if not args.no_gemini and gemini_classifier.enabled else 'Disabled / Offline'}")
    print("=" * 75 + "\n")

    def on_event_received(event: NormalizedEvent, session_features: SessionFeatures):
        # 1. Rule Analysis
        rule_res = rule_classifier.classify(event, session_features)

        # 2. Hybrid Classification
        hybrid_res = hybrid_classifier.classify(event, session_features)

        # 3. Deterministic Risk Evaluation
        risk_res = risk_engine.evaluate(event, hybrid_res, session_features)

        # 4. Session Intelligence Update
        session_profile = session_intelligence_engine.update_session(event, hybrid_res, session_features)

        # Formatted diagnostic report
        print("=" * 75)
        print("[EVENT INGESTED]")
        print(f"  Session ID    : {event.session_id}")
        print(f"  Event Type    : {event.event_type}")
        if event.command:
            print(f"  Command       : {event.command}")
        if event.username:
            print(f"  Username      : {event.username}")
        print(f"  Source IP     : {event.source_ip or 'N/A'}")
        print(f"  Timestamp     : {event.timestamp.isoformat()}")

        print("-" * 75)
        print("[RULE ANALYSIS]")
        print(f"  Intent        : {rule_res.intent}")
        print(f"  Attack Stage  : {rule_res.attack_stage}")
        print(f"  Confidence    : {rule_res.confidence:.2f}")
        if rule_res.rule_matches:
            print(f"  Rule Matches  : {', '.join(rule_res.rule_matches)}")
        if rule_res.evidence:
            print(f"  Rule Evidence : {rule_res.evidence[0]}")

        if hybrid_res.ai_reason:
            print("-" * 75)
            print("[GEMINI LLM ANALYSIS]")
            print(f"  AI Reason     : {hybrid_res.ai_reason}")
            if hybrid_res.ai_evidence:
                print(f"  AI Evidence   : {', '.join(hybrid_res.ai_evidence)}")

        print("-" * 75)
        print("[FINAL HYBRID CLASSIFICATION]")
        print(f"  Final Intent  : {hybrid_res.intent}")
        print(f"  Attack Stage  : {hybrid_res.attack_stage}")
        print(f"  Confidence    : {hybrid_res.confidence:.2f}")
        print(f"  Decision Provenance: {hybrid_res.source}")

        print("-" * 75)
        print("[DETERMINISTIC RISK ASSESSMENT]")
        print(f"  Event Risk Score: {risk_res.risk_score}/100 [{risk_res.severity}]")
        for factor in risk_res.contributing_factors:
            print(f"    • {factor}")

        print("-" * 75)
        print("[SESSION ATTACKER PROFILE]")
        print(f"  Dominant Intent : {session_profile.dominant_intent}")
        print(f"  Furthest Stage  : {session_profile.current_attack_stage}")
        print(f"  Cumulative Risk : {session_profile.risk_score}/100 [{session_profile.severity}]")
        print(f"  Intent Trajectory: {' -> '.join(session_profile.intent_sequence[-6:])}")
        print("=" * 75 + "\n", flush=True)

    collector = AsyncLogCollector(
        log_path=args.log_path,
        aggregator=aggregator,
        from_beginning=args.from_beginning
    )
    collector.register_callback(on_event_received)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(collector.start())
    except KeyboardInterrupt:
        print("\n[*] Stopping classification engine gracefully...")
        collector.stop()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
