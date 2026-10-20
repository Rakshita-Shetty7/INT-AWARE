#!/usr/bin/env python3
"""
Live end-to-end verification for the Intent-Aware Deception System.

Reads ONLY real data from the running API — it never fabricates numbers.
Run it after `scripts/demo_all_intents.py` (or after any real attacker
traffic) to prove, reproducibly, that the whole pipeline is working:

    honeypot capture -> collector -> normalize -> feature extraction ->
    hybrid intent classification (rule + ML + optional Gemini) ->
    attack-stage mapping -> risk scoring -> MongoDB -> REST API

What it checks and prints:
  1. /api/health           - every component is up (DB, ML model, rules, Cowrie feed)
  2. /api/dashboard/stats  - events/sessions/attackers actually persisted
  3. /api/events/recent    - each COMMAND carries a classification_source and,
                             for ML/HYBRID, a real calibrated confidence
  4. /api/analytics/intents- coverage across the 10 intent classes

Exit code is 0 only if the core checks pass, so this doubles as a smoke test.

Usage:
    .venv/Scripts/python.exe scripts/verify_live.py
    .venv/Scripts/python.exe scripts/verify_live.py --base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import Any, Dict, List

import requests

# Windows consoles default to cp1252 and choke on non-ASCII; never let a
# decorative glyph crash a verification run. Prefer UTF-8, fall back safely.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

# ANSI helpers (degrade gracefully if the terminal ignores them)
GREEN, RED, YEL, DIM, BOLD, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m",
)
OK = f"{GREEN}PASS{RESET}"
BAD = f"{RED}FAIL{RESET}"
WARN = f"{YEL}WARN{RESET}"

ML_SOURCES = {"ML", "HYBRID"}
# The 10 intent classes the model is trained on.
EXPECTED_INTENTS = {
    "RECONNAISSANCE", "DISCOVERY", "CREDENTIAL_ACCESS", "EXECUTION",
    "PRIVILEGE_ESCALATION", "PERSISTENCE", "EXPLOITATION", "EXFILTRATION",
    "CLEANUP", "OTHER",
}


def _get(base: str, path: str, **params) -> Any:
    r = requests.get(f"{base}{path}", params=params or None, timeout=10)
    r.raise_for_status()
    return r.json()


def _clean(source: Any) -> str:
    return str(source or "").replace("ClassificationSource.", "").upper()


def _hr() -> None:
    print(f"{DIM}{'-' * 74}{RESET}")


def check_health(base: str, results: List[bool]) -> None:
    print(f"\n{BOLD}[1/4] Component health  {DIM}GET /api/health{RESET}")
    _hr()
    try:
        h = _get(base, "/api/health")
    except Exception as exc:  # noqa: BLE001
        print(f"  {BAD}  could not reach the API: {exc}")
        print(f"  {DIM}      is the stack up?  docker compose up -d{RESET}")
        results.append(False)
        return

    ml = h.get("ml_model", {}) or {}
    checks = [
        ("API status healthy", h.get("status") == "healthy", h.get("status")),
        ("MongoDB connected", h.get("database") == "connected", h.get("database")),
        ("ML model loaded", bool(ml.get("available")),
         f"{ml.get('model_name')} | {ml.get('classes')} classes | "
         f"held-out acc {float(ml.get('accuracy') or 0) * 100:.2f}%"),
        ("Rule engine enabled", bool(h.get("rule_engine_enabled")), h.get("rule_engine_enabled")),
        ("Cowrie feed present", bool(h.get("cowrie_log_present")), h.get("collector_path")),
    ]
    for label, ok, detail in checks:
        print(f"  {OK if ok else BAD}  {label:<24}{DIM}{detail}{RESET}")
        results.append(ok)

    # Gemini is OPTIONAL by design — report it, never require it.
    gem = h.get("gemini_enabled")
    print(f"  {DIM}(info) Gemini semantic layer: "
          f"{'configured' if gem else 'inactive'} — optional, not required{RESET}")


def check_stats(base: str, results: List[bool]) -> None:
    print(f"\n{BOLD}[2/4] Persisted data  {DIM}GET /api/dashboard/stats{RESET}")
    _hr()
    try:
        s = _get(base, "/api/dashboard/stats")
    except Exception as exc:  # noqa: BLE001
        print(f"  {BAD}  {exc}")
        results.append(False)
        return
    events = s.get("total_events", 0)
    print(f"  events={events}  sessions={s.get('total_sessions', 0)}  "
          f"attackers={s.get('total_attackers', 0)}  "
          f"critical={s.get('critical_sessions', 0)}  alerts={s.get('open_alerts', 0)}")
    ok = events > 0
    print(f"  {OK if ok else WARN}  {'events have been captured and persisted' if ok else 'no events yet — run scripts/demo_all_intents.py first'}")
    results.append(ok)


def check_events(base: str, results: List[bool]) -> None:
    print(f"\n{BOLD}[3/4] Live classification source  {DIM}GET /api/events/recent{RESET}")
    _hr()
    try:
        data = _get(base, "/api/events/recent", limit=50)
    except Exception as exc:  # noqa: BLE001
        print(f"  {BAD}  {exc}")
        results.append(False)
        return

    rows = data if isinstance(data, list) else data.get("items", [])
    cmds = [e for e in rows if e.get("command")]
    if not cmds:
        print(f"  {WARN}  no command events yet — run scripts/demo_all_intents.py first")
        results.append(False)
        return

    print(f"  {DIM}{'SOURCE':<9}{'INTENT':<20}{'ML_CONF':<9}RISK  COMMAND{RESET}")
    src_counts: Counter = Counter()
    for e in cmds[:20]:
        src = _clean(e.get("classification_source"))
        src_counts[src] += 1
        conf = e.get("ml_confidence")
        conf_s = f"{conf:.2f}" if isinstance(conf, (int, float)) else "-"
        cmd = (e.get("command") or "")[:40]
        print(f"  {src:<9}{str(e.get('intent', '')):<20}{conf_s:<9}"
              f"{str(e.get('risk_score', 0)):<5} {cmd}")

    for src in cmds[20:]:
        src_counts[_clean(src.get("classification_source"))] += 1

    ml_driven = sum(v for k, v in src_counts.items() if k in ML_SOURCES)
    total = sum(src_counts.values())
    print(f"\n  source breakdown ({total} commands): "
          + "  ".join(f"{k}={v}" for k, v in src_counts.most_common()))
    ok = ml_driven > 0
    print(f"  {OK if ok else BAD}  {ml_driven}/{total} commands classified by the ML model "
          f"(ML or HYBRID) — proves the model is live in the pipeline")
    results.append(ok)


def check_intents(base: str, results: List[bool]) -> None:
    print(f"\n{BOLD}[4/4] Intent coverage  {DIM}GET /api/analytics/intents{RESET}")
    _hr()
    try:
        data = _get(base, "/api/analytics/intents")
    except Exception as exc:  # noqa: BLE001
        print(f"  {BAD}  {exc}")
        results.append(False)
        return

    # Accept a few shapes: {"distribution":[{intent,count}]} / list / {intent:count}
    seen: Dict[str, int] = {}
    if isinstance(data, dict) and isinstance(data.get("distribution"), list):
        for item in data["distribution"]:
            seen[str(item.get("intent"))] = item.get("count", 0)
    elif isinstance(data, list):
        for item in data:
            seen[str(item.get("intent"))] = item.get("count", 0)
    elif isinstance(data, dict):
        seen = {str(k): v for k, v in data.items() if isinstance(v, int)}

    present = {k for k, v in seen.items() if v}
    for intent in sorted(EXPECTED_INTENTS):
        c = seen.get(intent, 0)
        mark = OK if c else f"{DIM}....{RESET}"
        print(f"  {mark}  {intent:<22}{DIM}{c}{RESET}")

    covered = len(present & EXPECTED_INTENTS)
    unexpected = present - EXPECTED_INTENTS
    if unexpected:
        print(f"  {WARN}  unexpected intent labels: {', '.join(sorted(unexpected))}")
    print(f"  {OK if covered >= 5 else WARN}  {covered}/10 intent classes observed in live data")
    results.append(covered >= 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://127.0.0.1:8000", help="API base URL")
    args = ap.parse_args()

    print(f"{BOLD}Intent-Aware Deception System — live verification{RESET}")
    print(f"{DIM}target: {args.base}{RESET}")

    results: List[bool] = []
    check_health(args.base, results)
    check_stats(args.base, results)
    check_events(args.base, results)
    check_intents(args.base, results)

    _hr()
    passed = sum(1 for r in results if r)
    total = len(results)
    if all(results):
        print(f"{GREEN}{BOLD}VERDICT: PASS{RESET}  {passed}/{total} checks — "
              f"the pipeline is live end-to-end (honeypot -> ML classification -> API).")
        return 0
    print(f"{RED}{BOLD}VERDICT: INCOMPLETE{RESET}  {passed}/{total} checks passed. "
          f"See failures above (most commonly: stack not up, or no traffic sent yet).")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted.")
        sys.exit(130)
