# INT-AWARE — Remediation & Enhancement Roadmap

**Companion to:** `PROJECT_AUDIT.md` (read that first — every phase here traces to a finding ID `Fn` from the audit's §12 register).
**Sequencing principle:** correctness & integrity (P0) → reliability (P1) → capability & hardening (P2) → observability/benchmarks (P3) → docs/cosmetic (P4–P5). Later phases depend on earlier ones; do not reorder without re-checking dependencies.
**Non-negotiables carried from the directive into every phase:**
- No fabricated data, metrics, or benchmarks. If a target number cannot be scientifically achieved, report the real one.
- The honeypot must never execute attacker-controlled input on the host. Treat all attacker input as malicious data.
- The LLM is an *optional* layer: sanitize input, prevent prompt injection, constrain & validate output, never execute model-generated commands.
- Every displayed value must originate from real system data.

Each phase lists **Objective · Addresses · Files · Dependencies · Implementation · Tests · Success criteria (measurable)**. Success criteria are pass/fail gates, not aspirations.

---

## PHASE 0 — Reproducibility & Safety Baseline  **(P0)**

**Objective:** Establish a real, isolated version history and a CI gate before *any* code changes, so every later phase is reproducible and reviewable.

**Addresses:** F4 (no git history, repo rooted at `$HOME`), F11 (no CVE scan / mutable tags — baseline only).

**Files:** `.git` (new, inside project), `.github/workflows/ci.yml` (new), `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `requirements-dev.txt`.

**Dependencies:** none (must be first).

**Implementation:**
1. `git init` **inside** `INT-AWARE/`; verify `git rev-parse --show-toplevel` now points at the project, not `$HOME`. Confirm `.gitignore` covers `.env*`, `.venv`, `node_modules`, `cowrie.json*`, `var/`, artifacts as appropriate.
2. Initial commit of the current tree **plus** `PROJECT_AUDIT.md` + `ROADMAP.md` as the reproducibility anchor.
3. CI workflow: install `requirements-dev.txt`, run `pytest -q`, run `pip-audit` (non-blocking to start, blocking by Phase 10), lint. Cache the venv.
4. Record the exact toolchain (Python, sklearn, numpy versions) in the commit; these already exist in `metrics.json` — cross-reference.

**Tests:** CI runs green on the untouched suite (74/74). `git status` from `$HOME` no longer shows the project as untracked-in-home.

**Success criteria:**
- `git rev-list --count HEAD` ≥ 1 and `show-toplevel` = project dir. ✅/❌
- CI pipeline exists and passes on a clean checkout. ✅/❌
- No secret files staged (`git ls-files | grep -E '\.env$'` returns nothing). ✅/❌

---

## PHASE 1 — Repair the Alert Subsystem  **(P0)**

**Objective:** Make alerts actually fire, driven by the correct (session-level cumulative) risk score, with tests that exercise the *real* engine path.

**Addresses:** F1 (alert subsystem structurally unreachable).

**Files:** `backend/app/pipeline.py` (:127), `backend/app/services/persistence_service.py` (:102, dashboard stats :423), `backend/app/models/database.py` (:107), `backend/app/services/session_intelligence.py`, `backend/app/services/risk_engine.py`, `tests/test_risk_engine.py`, `tests/test_persistence_service.py`, `tests/test_e2e_pipeline.py`.

**Dependencies:** Phase 0.

**Implementation (decision required — see note):**
1. Introduce an explicit **alerting score** = the session-level cumulative risk from `SessionIntelligenceEngine` (range 0–100, already reaches ≥75), *not* the event-level `RiskEngine` score (ceiling 65 by design — keep it as a per-event explainable signal).
2. Change both alert gates (`pipeline.py:127`, `persistence_service.py:102`) to consume the session cumulative score. Keep the ≥75 CRITICAL threshold, or make it a named config constant `ALERT_THRESHOLD`.
3. Reconcile `AlertDoc` schema: `risk_score` should reference the alerting score's range; keep `ge=…` consistent with `ALERT_THRESHOLD` (don't hardcode two different numbers in two files).
4. Fix `get_dashboard_stats.open_alerts` to reflect real alerts once they can exist.
5. **Do not** simply inflate event weights to cross 75 — that would corrupt the explainable event-risk model. The fix is *which score drives alerts*, not making event risk bigger.

**Tests:**
- New regression test: feed a realistic multi-stage session **through the real pipeline** (normalize → aggregate → classify → session intelligence → persist) and assert an alert row is created and a WS alert is broadcast. This is the test the current suite lacks (the existing "alert on critical" test bypasses the engine — replace it).
- Assert `open_alerts` > 0 after that session; assert event-risk-only sessions below threshold do **not** alert.

**Success criteria:**
- A scripted attack session produces ≥1 persisted alert and ≥1 `/ws/alerts` broadcast. ✅/❌
- The regression test drives the score through the real engines (no direct `risk_score=` injection). ✅/❌
- No two files disagree on the alert threshold value. ✅/❌

---

## PHASE 2 — Scientific-Integrity Reconciliation  **(P0)**

**Objective:** Make every published number and claim match what the code/artifacts actually produce. Either the ML/Gemini paths genuinely decide cases, or the prose is corrected to say they don't.

**Addresses:** F2 (optimistic accuracy framing), F3 (CSVs contradict prose; no latency percentiles), F14 (doc drift).

**Files:** `scripts/evaluate_phase9.py`, `scripts/evaluate_phase10.py`, `scripts/generate_eval_assets.py`, `docs/evaluation/*`, `docs/FINAL_REPORT.md`, `README.md`, `backend/app/ml/artifacts/metrics.json` (read-only reference — do not hand-edit).

**Dependencies:** Phase 0. (Independent of Phase 1.)

**Implementation:**
1. **Diagnose why `classification_source` is only ever RULE/FALLBACK** in the shipped CSVs. Likely the rule engine's high-confidence threshold pre-empts ML on every labeled sample. Decide intentionally: (a) lower rule precedence for evaluation so ML/hybrid actually decide, and re-run; or (b) keep rules primary and **rewrite the prose** to state that rules decide the labeled set and ML is the fallback tier. Either is honest; the current mismatch is not.
2. **Foreground the honest metric.** Lead all docs with the leave-families-out figure (accuracy 0.6787 / macro-F1 0.5267) as the *generalization* number, and clearly label 0.9449 as same-template (optimistic). Keep both; never drop the honest one.
3. **Latency:** produce p50/p95/p99 on documented hardware; replace "sub-millisecond ML path" with measured numbers or delete the claim. Record CPU/RAM/OS in the report.
4. Fix drift: pymongo (not Motor), Python 3.13 (match Dockerfile).
5. Regenerate `docs/evaluation/*` from scripts so CSVs and prose are produced by the same run (no hand-authored numbers).

**Tests:** A `scripts/` regeneration run reproduces the committed CSVs/metrics within tolerance from a fixed seed; a doc-lint check greps for banned phrases ("99.89", "sub-millisecond", "Motor") and fails if reintroduced without evidence.

**Success criteria:**
- Every accuracy figure in docs is labeled with its split; the honest figure appears first. ✅/❌
- `classification_source` distribution in CSVs matches the prose description exactly. ✅/❌
- Latency reported as p50/p95/p99 + hardware, or the claim is removed. ✅/❌
- No banned/unsupported phrase survives the doc-lint. ✅/❌

---

## PHASE 3 — Reliability Hardening  **(P1)**

**Objective:** Remove the ways the running system can hang, leak memory, or silently lose state.

**Addresses:** F5 (Gemini timeout unenforced), F6 (unbounded growth / state loss), F7 (O(n) attacker recompute).

**Files:** `backend/app/services/gemini_classifier.py` (:156), `backend/app/services/gemini_session_analyst.py`, `backend/app/services/log_collector.py` (:42), `backend/app/services/session_intelligence.py`, `backend/app/services/persistence_service.py` (:273).

**Dependencies:** Phase 0. (Independent of 1–2.)

**Implementation:**
1. **Enforce the timeout:** pass a per-request timeout / `http_options` to `generate_content()` in both Gemini services, or wrap the call in a bounded executor future. Prove it: a mocked slow client returns within timeout + margin.
2. **Bound `_processed_event_ids`:** switch to a bounded LRU/deduplication window (dedup only needs recent history because the tailer is ordered) — or persist the high-water offset instead of an ever-growing set.
3. **Persist/evict session-intelligence state:** either back `_session_classifications`/`_session_profiles` with Mongo (recover on restart) or add TTL eviction; document the chosen semantics.
4. **Incremental attacker aggregation:** replace full recompute in `update_attacker` with an incremental update (maintain running counters per IP) so cost is O(1) per event.

**Tests:** timeout enforcement test (mock slow SDK); memory-bound test (feed N duplicate ids, assert set/window stays bounded); restart-recovery test for session state (if persistence chosen); attacker-aggregation test asserting incremental result equals full-recompute result.

**Success criteria:**
- A hung Gemini call returns/aborts within `GEMINI_TIMEOUT` + margin. ✅/❌
- Dedup memory is bounded under a stream of ≥100k events. ✅/❌
- `update_attacker` is O(1) per event (no per-event full scan); parity test passes. ✅/❌

---

## PHASE 4 — Novelty / OOD / Abstention  **(P1)**

**Objective:** Let the system say "I don't know." Introduce KNOWN / AMBIGUOUS / LOW-CONFIDENCE / NOVEL/OOD outcomes instead of always forcing one of 10 classes.

**Addresses:** F8 (no novelty/OOD/abstention — part 1).

**Files:** `backend/app/services/hybrid_classifier.py`, `backend/app/ml/intent_ml_classifier.py`, `backend/app/models/intent.py`, new `backend/app/services/novelty_detector.py`, `docs/evaluation/unseen/*` (already has Type A novel / B low-confidence / C wrong-intent / D benign).

**Dependencies:** Phase 2 (need honest calibration first), Phase 0.

**Implementation:**
1. Use the calibrated classifier's max-probability + margin to define **LOW-CONFIDENCE** (abstain) and **AMBIGUOUS** (top-2 within δ) bands; expose thresholds as config.
2. Add an **OOD score** (e.g. distance in TF-IDF space to training centroids, or a one-class model over training features) → **NOVEL** when beyond threshold.
3. Extend the intent result model with a `determination` enum {KNOWN, AMBIGUOUS, LOW_CONFIDENCE, NOVEL} and surface it through the API/dashboard.
4. Wire the existing `unseen_dataset.csv` classes to validate: Type A→NOVEL, Type B→LOW_CONFIDENCE, Type C→ideally not confidently wrong, Type D→OTHER/benign.

**Tests:** unit tests per band using the unseen dataset; assert Type A flagged NOVEL at target recall; assert calibration (confidence buckets vs empirical accuracy).

**Success criteria:**
- Type A (novel) detected as NOVEL at ≥ an agreed recall (report the real number). ✅/❌
- Confidence is calibrated (report ECE/reliability, don't fabricate). ✅/❌
- No regression in KNOWN-class accuracy beyond an agreed tolerance. ✅/❌

---

## PHASE 5 — Sequence Intelligence & Predictive Next-Intent  **(P1)**

**Objective:** Model the attack as a sequence, track real stage transitions, and predict the likely next intent — labeled OBSERVED / INFERRED / PREDICTED so nothing invented is shown as fact.

**Addresses:** F8 (no predictive next-intent / no transition modeling — part 2).

**Files:** `backend/app/services/session_intelligence.py`, new `backend/app/services/sequence_model.py`, `backend/app/models/session_intelligence.py`, API sessions router, frontend session view.

**Dependencies:** Phase 4 (determinations feed the sequence), Phase 1 (session risk wiring).

**Implementation:**
1. Replace "furthest stage in fixed order" with a **transition model** (empirical transition-frequency matrix over observed intent sequences, or a lightweight sequence model) built from the dataset.
2. Predict next intent with a probability; **label provenance**: OBSERVED (already happened), INFERRED (deduced from current state), PREDICTED (model forecast) — never render a prediction as observed fact.
3. Surface top-k predicted next intents with probabilities in the session API + dashboard.

**Tests:** transition-matrix correctness on a synthetic sequence; prediction provenance labeling; top-k prediction sanity on held-out sequences (report real hit-rate).

**Success criteria:**
- Next-intent prediction present with calibrated probability and explicit provenance label. ✅/❌
- Predicted-next hit-rate reported honestly on held-out sessions. ✅/❌

---

## PHASE 6 — Decomposable Risk Engine v2 & Alert Prioritization  **(P1)**

**Objective:** Unify event- and session-level risk into one explainable, decomposable model whose contributions are inspectable, and prioritize alerts by it.

**Addresses:** F1 follow-through (alert prioritization), capability gap "decomposable risk."

**Files:** `backend/app/services/risk_engine.py`, `backend/app/services/session_intelligence.py`, `backend/app/models/risk.py`, `backend/app/api/routers/alerts.py`, frontend alerts view.

**Dependencies:** Phase 1, Phase 5.

**Implementation:**
1. Formalize risk as a documented sum of labeled contributions (intent base, escalation signals, novelty bump, sequence risk), each returned with its magnitude so the UI can show *why*.
2. Alert **priority** = function of session risk + novelty + stage advancement; expose an ordered alert feed.
3. Keep event-risk explainable and bounded; session-risk drives alerting (from Phase 1).

**Tests:** contribution decomposition sums to the total; priority ordering is deterministic for fixed inputs; boundary tests for each severity.

**Success criteria:**
- Every risk score returns an itemized, summable breakdown. ✅/❌
- Alerts are ordered by a documented priority function. ✅/❌

---

## PHASE 7 — Attacker Profiling & MITRE Depth  **(P2)**

**Objective:** Turn per-IP aggregation into behavioral profiling, and deepen ATT&CK mapping beyond flat technique IDs.

**Addresses:** capability gaps (attacker profiling, MITRE depth); builds on F7 fix.

**Files:** `backend/app/services/persistence_service.py`, `backend/app/services/mitre_mapper.py`, new `backend/app/services/attacker_profiler.py`, attackers router, frontend attacker view.

**Dependencies:** Phase 3 (incremental aggregation), Phase 5.

**Implementation:**
1. Behavioral features per attacker (intent mix, stage reach, tempo, novelty rate); optional clustering into profile archetypes (report cluster validity honestly; don't over-claim).
2. MITRE: map intents→tactics→techniques→sub-techniques where evidence supports it; add a coverage view. Cite the ATT&CK version.

**Tests:** profiler feature correctness; MITRE mapping unit tests with known technique IDs; no fabricated technique attributions.

**Success criteria:**
- Attacker profile derived only from real observed events. ✅/❌
- MITRE mappings are evidence-backed and versioned. ✅/❌

---

## PHASE 8 — Security Hardening  **(P2)**

**Objective:** Add the authentication, transport security, and headers required before this could run anywhere but loopback.

**Addresses:** F9 (no auth/TLS/headers; CORS too broad), F11 (root containers, mutable tags).

**Files:** `backend/app/main.py` (CORS), new auth dependency, `frontend/nginx.conf`, `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`.

**Dependencies:** Phase 0.

**Implementation:**
1. API auth (token/API-key or session) on all mutating and sensitive endpoints; origin check + connection cap on WebSockets.
2. Tighten CORS to explicit origins (drop the any-localhost-port regex for non-dev).
3. nginx: add CSP, X-Frame-Options, `X-Content-Type-Options: nosniff`, Referrer-Policy, HSTS (behind TLS), `server_tokens off`, rate limiting.
4. Containers: add non-root `USER`, `cap_drop`, `no-new-privileges`, resource limits; pin base images by digest.

**Tests:** auth-required tests (401/403 without creds); CORS tests; header-presence tests; container smoke test as non-root.

**Success criteria:**
- Sensitive endpoints reject unauthenticated requests. ✅/❌
- Security headers present; containers run as non-root; images digest-pinned. ✅/❌

---

## PHASE 9 — Adversarial-Robustness Gate  **(P2)**

**Objective:** Promote the offline unseen/adversarial evaluation into a CI gate with honest robustness metrics.

**Addresses:** F10 (adversarial/robustness offline-only), directive's adversarial-robustness requirement.

**Files:** `scripts/evaluate_phase10.py`, `tests/` (new robustness test), `.github/workflows/ci.yml`, `docs/evaluation/unseen/*`.

**Dependencies:** Phase 4 (novelty), Phase 2 (honest eval harness).

**Implementation:**
1. Wire the unseen dataset (Type A/B/C/D) into a CI-run robustness evaluation producing NOVEL-recall, low-confidence-recall, wrong-intent-rate, benign-FPR.
2. Add obfuscation/adversarial perturbations (whitespace, encoding, synonymic commands) and measure degradation honestly.
3. Gate: fail CI if robustness drops below a committed baseline (set from the first honest run, not an aspirational target).

**Tests:** the robustness script runs in CI and emits a metrics artifact; regression gate compares to baseline.

**Success criteria:**
- Robustness metrics generated in CI every run and stored. ✅/❌
- A committed baseline exists and gates regressions (real numbers). ✅/❌

---

## PHASE 10 — Test-Suite Expansion & ML-Regression  **(P2)**

**Objective:** Close the coverage gaps the audit found, especially the entirely-untested ML stack.

**Addresses:** F10, F15, and the "ML stack untested / hybrid uses `_StubML`" finding.

**Files:** `tests/` (new: ML classifier load+predict, train/split/dataset/labels, pipeline orchestration, security tests, `GET /api/events/recent`), `.github/workflows/ci.yml`.

**Dependencies:** Phases 1–4 (test the new behavior too).

**Implementation:**
1. Load the real `.joblib` in a test and assert predictions on fixed inputs; add a **model-regression** test that fails if accuracy on a frozen holdout drops below the committed metric.
2. Test `train`/`split`/`dataset`/`labels` (determinism, family-aware split, no leakage).
3. Add security tests (auth, injection-as-data, CORS), pipeline-orchestration tests, and the missing endpoint test.
4. Make `pip-audit` blocking now.

**Tests:** (this phase *is* tests) — target a coverage floor and enforce it in CI.

**Success criteria:**
- ML stack has direct tests incl. a model-regression gate tied to `metrics.json`. ✅/❌
- All 20 router endpoints covered. ✅/❌
- CI coverage ≥ committed floor; `pip-audit` blocking. ✅/❌

---

## PHASE 11 — Observability & Honest Benchmarks  **(P3)**

**Objective:** Make the running system inspectable and produce defensible performance numbers.

**Addresses:** capability gaps (observability, p50/p95/p99), reinforces F3.

**Files:** `backend/app/main.py`, new `backend/app/observability/` (structured logging, metrics), `scripts/benchmark.py`, `docs/`.

**Dependencies:** Phases 1, 3, 6.

**Implementation:**
1. Structured logging with correlation ids across ingest→classify→persist; counters/histograms for throughput and per-stage latency.
2. A benchmark harness that reports p50/p95/p99 ingestion and classification latency and sustained events/sec **on documented hardware**, seeds fixed, methodology written down.
3. `/metrics`-style endpoint (auth-gated per Phase 8).

**Tests:** benchmark harness runs deterministically; metrics endpoint returns real counters.

**Success criteria:**
- p50/p95/p99 + throughput reported with hardware + method (no fabricated figures). ✅/❌
- Per-stage latency observable at runtime. ✅/❌

---

## PHASE 12 — Analyst Dashboard & Documentation Rewrite  **(P3–P5)**

**Objective:** Present the new intelligence in the UI and rewrite all documentation to match the (now honest, now working) system.

**Addresses:** F13 (misleading fallbacks), F14 (doc drift), dashboard/analyst views, defensible research writeup.

**Files:** `frontend/src/**`, `README.md`, `docs/FINAL_REPORT.md`, `RUN.md`.

**Dependencies:** Phases 1–11 (UI shows their outputs).

**Implementation:**
1. Fix misleading fallbacks: null IP → "unknown", missing protocol → "unknown" (never invent 127.0.0.1/SSH).
2. Add/verify analyst views for: alerts (prioritized), determinations (KNOWN/NOVEL/…), next-intent predictions with provenance, risk decomposition, attacker profiles, MITRE coverage, robustness/eval summary. (Enumerate against the target view list; build what's missing, all fed by real API data.)
3. Rewrite docs to state real accuracy (both splits, honest first), real latency, pymongo (not Motor), the alerting model, and the research contribution — with the audit's findings as the honest baseline "before."

**Tests:** frontend renders each view from mocked-but-real-shaped API responses; a fabrication-scan (no `Math.random`, no hardcoded stats) stays green; doc-lint (Phase 2) stays green.

**Success criteria:**
- Every dashboard value traces to a real API field; no invented fallbacks. ✅/❌
- Docs contain no unsupported claim; both accuracy splits shown, honest one first. ✅/❌
- Target analyst views present and populated from live data. ✅/❌

---

## Dependency Graph (quick reference)

```
P0 ──┬─► P1 ──► P6 ──► P11 ──► P12
     ├─► P2 ──► P4 ──► P5 ──┘        (P5 also needs P1)
     ├─► P3 ──► P7                    (P7 needs P5)
     ├─► P8
     └─► P4 ──► P9                    (P9 needs P2)
                P10 needs P1–P4
```

## Global "definition of done" (applies to every phase)
1. All existing tests still green; new tests for the phase added and green in CI.
2. No fabricated numbers introduced; any metric shown is reproducible from a committed script + seed.
3. Honeypot host-safety invariant re-verified (no new exec/subprocess path).
4. LLM remains optional, sanitized, schema-validated, output-only.
5. Change committed with a message referencing the finding ID(s) it closes.
