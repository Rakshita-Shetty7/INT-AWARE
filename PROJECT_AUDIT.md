# INT-AWARE — Technical Audit

**Project:** INT-AWARE — Intent-Aware Deception System for Real-Time Attacker Profiling
**Audit date:** 2026-09-10
**Audit type:** Read-only, evidence-based. No source files were modified to produce this document.
**Method:** Full manual read-through of the backend; four scoped sub-audits (frontend, documentation/evaluation-claims, pytest suite, infra/deployment); direct reads of all honeypot and deployment configuration. Every claim below cites the file (and line, where a specific construct is referenced) that supports it. Where the repository does *not* contain evidence for a claimed capability, that is stated explicitly rather than assumed.

> **Scope note on honesty.** This audit reports what the repository actually contains. Where prose in the docs or paper asserts a capability or number the code/artifacts do not support, the discrepancy is documented as a finding — not smoothed over. No metric in this document has been invented; all figures are read verbatim from committed artifacts (`backend/app/ml/artifacts/metrics.json`, the evaluation CSVs) and labeled with the split that produced them.

---

## 1. Executive Summary

INT-AWARE is a honeypot-telemetry intent-classification and attacker-profiling system: a real Cowrie SSH honeypot writes JSON event logs, a FastAPI backend tails those logs, classifies each event's attacker *intent* (10-class taxonomy) via a rule → ML → optional-Gemini hybrid, scores risk, aggregates per-session and per-attacker intelligence into MongoDB, and streams results to a React dashboard over REST + WebSockets.

**The engineering core is real and, in several places, genuinely well-built.** The honeypot is safely isolated; the log tailer is rotation- and truncation-aware; the classifier arbitration is coherent; the risk engine is additive and explainable; MongoDB indexes exist; the test suite is hermetic and green (74/74); and the frontend contains **no fabricated data** — a direct, verified pass on the "no fake features" mandate for the UI layer.

**However, the project has correctness, integrity, and completeness gaps that block a research-grade claim as-is:**

1. **The alert subsystem is structurally unreachable.** Event-level risk maxes out at **65**; every alert trigger and the alert schema require **≥ 75**. No alert can ever fire. (P0 — §5.1)
2. **The headline accuracy is split-dependent and the honest number is much lower.** Same-template split = **94.49%**; leave-families-out (true generalization) = **67.87%**. There is *no* "99.89%" anywhere in the repo (good — it was never fabricated), but the docs foreground the optimistic figure. (P0 — §7)
3. **Shipped evaluation artifacts contradict prose claims.** The per-sample CSVs show the deciding classifier was *only ever* the rule engine or a deterministic fallback — the ML/hybrid/Gemini paths never actually decided a labeled evaluation case, despite text claiming they did. (P0 — §7.3)
4. **No version history / repo rooted at `$HOME`.** Zero git commits; the git root is `C:/Users/raksh`. Not reproducible, and a real accidental-secret-exposure risk. (P0 — §9.1)
5. **The configured LLM timeout is never enforced,** so a hung Gemini call stalls ingestion. (P1 — §6.3)
6. **Several headline "intelligence" capabilities implied by the project's framing do not exist yet:** no novelty/out-of-distribution detection or abstention (the classifier *always* returns one of 10 classes), no predictive next-intent, no real stage-transition modeling, no adversarial-robustness gate in CI, no latency percentiles. (§8)

None of these are unfixable; most are surgical. The rest of this document is the evidence base for a remediation roadmap.

---

## 2. Repository Structure & Provenance

### 2.1 Layout (as read)

```
INT-AWARE/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app + pipeline bootstrap (own thread/loop)
│   │   ├── config.py                   # env-driven Settings + Gemini-key validator
│   │   ├── pipeline.py                 # process_event(): classify→risk→session→persist→broadcast
│   │   ├── api/routers/                # health, dashboard, events, sessions, attackers, alerts, analytics, websocket
│   │   ├── database/mongodb.py         # sync pymongo manager + index creation
│   │   ├── models/                     # Pydantic: events, features, intent, risk, session_intelligence, database, api
│   │   ├── ml/
│   │   │   ├── intent_ml_classifier.py # MLIntentClassifier singleton (loads joblib)
│   │   │   ├── train.py, split.py, dataset.py, labels.py
│   │   │   └── artifacts/              # intent_classifier.joblib, metrics.json
│   │   └── services/                   # normalizer, feature_extractor, aggregator, rule/ML/gemini/hybrid
│   │                                   #   classifiers, risk_engine, session_intelligence,
│   │                                   #   session analyst, mitre_mapper, log_collector, persistence, ws manager
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                           # React 19 / Vite, nginx.conf, Dockerfile (multi-stage)
├── honeypot/etc/                       # cowrie.cfg (stock dist), userdb.txt (deliberate weak creds)
├── scripts/                            # evaluate_phase9.py, evaluate_phase10.py, generate_eval_assets.py
├── tests/                              # 74 pytest tests
├── docs/                               # README, FINAL_REPORT, evaluation/ (CSVs + reports)
├── docker-compose.yml
├── .env / .env.example                 # byte-identical; placeholder key only
└── .gitignore
```

### 2.2 Provenance findings

| Finding | Evidence | Severity |
|---|---|---|
| **Zero git commits.** `git rev-list --count HEAD` → *fatal: HEAD unknown revision*. | infra sub-audit, direct git query | **P0** |
| **Git root is the home directory,** not the project. `git rev-parse --show-toplevel` → `C:/Users/raksh`. `docker-compose.yml`, `.env.example` are untracked. | infra sub-audit | **P0** |
| `.gitignore` is sound: ignores `.env*`, `cowrie.json*`, `var/`, `node_modules`, `.venv`, logs. `.env` is git-ignored (`.gitignore:2`) and untracked. | infra sub-audit | (mitigant) |

**Consequence:** a careless `git add -A` from `$HOME` would stage the entire home directory (`.ssh/`, `.aws`, `.docker/config.json`, browser profiles). There is also no history to reproduce results from. This must be fixed before any reproducibility or MLOps claim.

---

## 3. Architecture & Data Flow

**End-to-end path (verified across `docker-compose.yml`, `log_collector.py`, `pipeline.py`, `persistence_service.py`):**

```
attacker/test client
      │  SSH (emulated)
      ▼
[cowrie]  backend=shell, listen 127.0.0.1:2222      ← honeypot, never executes on host (§10)
      │  writes cowrie.json (JSON lines)
      ▼
volume cowrie-logs ──(mounted :ro)──► [api]
      │
      ▼
AsyncLogCollector.start()  ── binary tail, rotation-safe ──►  EventNormalizer.normalize()
      │                                                             │  (JSON → NormalizedEvent, sha256 id)
      ▼                                                             ▼
SessionAggregator.add_event() ─► SessionFeatures        pipeline.process_event() [sync callback]
                                                             │
        ┌────────────────────────────────────────────────────┤
        ▼                        ▼                     ▼       ▼
  HybridClassifier         RiskEngine          SessionIntelligence   MITRE mapper
  (rule/ML/Gemini)      (event risk ≤65)      (cumulative ≤100)
        │                        │                     │
        └──────────────► PersistenceService.save_event() ──► MongoDB (events/sessions/attackers/alerts)
                                                             │
                                                             ▼
                                          WebSocketManager broadcast  +  REST routers ──► React dashboard
```

**Threading model (important, and correct):** the ingestion pipeline runs on a **dedicated daemon thread with its own asyncio event loop** ([main.py:43-62](backend/app/main.py:43)), *not* the Uvicorn request loop. The WebSocket manager is handed the main loop for cross-thread broadcast. Gate: `PIPELINE_ENABLED` ([main.py:83](backend/app/main.py:83)). **Implication:** a blocking classifier call stalls *ingestion*, not the REST API — this narrows (but does not eliminate) the impact of the unenforced Gemini timeout (§6.3).

---

## 4. Component-by-Component Assessment

### 4.1 Ingestion (strong)

- **`log_collector.py` (298 lines) — well-engineered.** Rotation-safe via `(st_dev, st_ino)` identity ([:100-103](backend/app/services/log_collector.py:100), [:182-195](backend/app/services/log_collector.py:182)); truncation-safe (`st_size < offset` → reopen, [:188](backend/app/services/log_collector.py:188)); binary reads so offsets match `os.stat().st_size` ([:137](backend/app/services/log_collector.py:137), [:166](backend/app/services/log_collector.py:166)); partial-line buffering ([:169-171](backend/app/services/log_collector.py:169)). Two concerns: (a) `_processed_event_ids` is an unbounded in-memory `set` ([:42](backend/app/services/log_collector.py:42)) that grows for the process lifetime; (b) the registered callback is invoked synchronously and awaited if it is a coroutine ([:63-65](backend/app/services/log_collector.py:63)) — so a slow classifier blocks the tail loop.
- **`event_normalizer.py` — safe and deterministic.** Parses a JSON line into a `NormalizedEvent`; computes a deterministic `sha256` `event_id`; returns `None` on malformed/empty input. **Never executes anything.** (Verified: covered by 7 strong unit tests.)
- **`feature_extractor.py` / `session_aggregator.py`** — compute session features (`command_count`, `activity_rate`, intervals, etc.) incrementally. `shlex.split` with a plain `.split()` fallback — tokenization only, no execution. (3 + 3 strong unit tests, exact-value assertions.)

### 4.2 Classification

- **`rule_classifier.py` (strong, and the *de-facto* production classifier).** Regex signatures across all 10 intent categories, emitting intent + attack stage + `confidence ≥ 0.85`. The `subprocess`/`eval`/`popen` tokens at [:110,:115](backend/app/services/rule_classifier.py:110) are **detection string-literals**, not calls. 10 strong unit tests, incl. benign controls → `OTHER`.
- **`intent_ml_classifier.py` — real trained artifact, but untested and rarely decisive.** `MLIntentClassifier` is a module singleton ([:141](backend/app/ml/intent_ml_classifier.py:141)) loading `artifacts/intent_classifier.joblib`. **No pytest exercises it** — the hybrid tests substitute a `_StubML` (test sub-audit). Per the evaluation CSVs, ML never actually decided a labeled case (§7.3).
- **`gemini_classifier.py` — good structured-output discipline, one real bug.** Uses `response_schema=GeminiClassification` + `response_mime_type="application/json"` + `temperature=0.1` ([:149-154](backend/app/services/gemini_classifier.py:149)) — solid prompt-injection mitigation (constrained, schema-validated output; [:168](backend/app/services/gemini_classifier.py:168) `model_validate`). **Bug:** `self.timeout` is stored ([:65](backend/app/services/gemini_classifier.py:65)) but **never passed** to `generate_content()` ([:156-160](backend/app/services/gemini_classifier.py:156)) — the configured 5 s timeout is inert. **Weak sanitization:** `sanitize_payload` masks only `-p <pass>` and `password=` ([:101-102](backend/app/services/gemini_classifier.py:101)); other secret shapes (tokens, `--password`, key material, `curl -u`) pass through.
- **`gemini_session_analyst.py`** — same unenforced-timeout bug; uses `response_mime_type="application/json"` but **no `response_schema`** (weaker structured-output guarantee than the event classifier). Deterministic fallback is genuine.
- **`hybrid_classifier.py` — coherent arbitration.** Priority: strong rule (≥0.90) → confident ML (≥0.40) → Gemini → best-available → `OTHER`. 8 strong behavioral tests (`assert_called_once` / `assert_not_called`). Caveat: the real ML model is stubbed in those tests.

### 4.3 Risk & session intelligence

- **`risk_engine.py` — explainable, additive, and capped at 65.** `INTENT_BASE_WEIGHTS` top out at EXFIL = 35; additive signals: login_failed +5, brute_force +10, burst +5, command_depth +5, variety +5. **Arithmetic ceiling = 35+5+10+5+5+5 = 65.** `map_severity`: <25 LOW, <50 MEDIUM, <75 HIGH, else CRITICAL. **Event risk can never be CRITICAL.** (Confirmed by test: `test_risk_engine.py` asserts `risk_score == 65` as the max.)
- **`session_intelligence.py` — cumulative score *can* reach 100, but is thin on "intelligence."** Score = sum of **unique** intent weights + multi-stage bonus (+15 if ≥2 advanced stages) + brute +10 + depth +5 + burst +5, clamped 0–100. **This is the score that *should* drive alerts.** Weaknesses: (a) in-memory `_session_classifications` / `_session_profiles` dicts grow unbounded and are not recovery-backed (state lost on restart); (b) "current stage" = the furthest stage in a *fixed* `STAGE_ORDER` — there is **no real transition modeling and no next-intent prediction**; only 1 unit test (happy path).

### 4.4 Persistence & API

- **`persistence_service.py` (615 lines) — genuine aggregations, one dead alert path, one scalability hotspot.**
  - Alert creation gated on **event** `risk.risk_score >= 75` ([:102](backend/app/services/persistence_service.py:102)) → never true (see §5.1).
  - `update_attacker` ([:273](backend/app/services/persistence_service.py:273)) recomputes **all** sessions for an IP on **every** event (called from `update_session`, [:229-230](backend/app/services/persistence_service.py:229)) → **O(sessions_per_ip) per event**; a scalability cliff under sustained load.
  - `get_dashboard_stats` ([:423](backend/app/services/persistence_service.py:423)): `open_alerts` counts alerts with status OPEN → **permanently ≈ 0** (no alerts exist); `critical_sessions` counts sessions with CRITICAL severity → *can* be > 0. All analytics are real Mongo aggregations (no hardcoding).
- **`mongodb.py` — indexes exist** ([create_indexes, :80](backend/app/database/mongodb.py:80)): events/sessions/attackers/alerts with `event_id` unique, `session_id`, `timestamp`, `source_ip`, `intent`, `severity`, `risk_score`. `serverSelectionTimeoutMS=3000`. (This corrects an earlier working note that claimed "no indexes.")
- **API routers** — all read-only `GET` except `POST /sessions/{id}/analyze` (on-demand Gemini, safe). Pagination capped `le=200`. **No authentication on any endpoint, including WebSockets** (no origin check, no connection cap). `GET /api/events/recent` ([events.py:60](backend/app/api/routers/events.py:60)) has no test.
- **`models/database.py`** — `AlertDoc.risk_score = Field(..., ge=75, le=100)` ([:107](backend/app/models/database.py:107)): the schema **doubly** locks alerts to ≥75, compounding §5.1.

### 4.5 Frontend (verified clean of fabrication)

From the frontend sub-audit (36 source files): **no `Math.random`, no hardcoded statistics, no fabricated metrics** — every displayed value traces to an API response. This is a direct pass on the "no fake features" mandate for the UI. **Two misleading fallbacks** to fix: a null source IP renders as `127.0.0.1`, and a missing protocol renders as `SSH` — these should render as "unknown," not plausible-but-invented defaults.

---

## 5. P0 — Correctness Findings

### 5.1 The alert subsystem is structurally unreachable

**Claim:** No alert can ever be created or broadcast, so the `alerts` collection is permanently empty, `/ws/alerts` never emits, and dashboard `open_alerts` is permanently ≈ 0.

**Proof (three independent gates, all requiring ≥ 75 against a score that maxes at 65):**

| Location | Gate | Ceiling of the score used |
|---|---|---|
| [pipeline.py:127](backend/app/pipeline.py:127) | `if risk.risk_score >= 75:` → WS alert | event risk, max **65** |
| [persistence_service.py:102](backend/app/services/persistence_service.py:102) | `if risk.risk_score >= 75:` → DB alert | event risk, max **65** |
| [models/database.py:107](backend/app/models/database.py:107) | `risk_score: Field(ge=75, le=100)` | event risk, max **65** |

The event-risk ceiling of 65 is proven arithmetically from `INTENT_BASE_WEIGHTS` + additive bonuses in [risk_engine.py](backend/app/services/risk_engine.py) and is asserted by `test_risk_engine.py` (`risk_score == 65` as maximum). Meanwhile the **session-level** cumulative score (`session_intelligence.py`) *does* reach ≥75 — the alert logic is simply wired to the wrong score. **Root cause:** alerts gate on event-level risk; they should gate on session-level cumulative risk (or the risk engine's ceiling must change). This is the single highest-value correctness fix.

> Note: `test_persistence_service.py` asserts an "alert auto-trigger on critical" — but it constructs a `RiskAssessment` with `risk_score` ≥ 75 *directly* in the test, bypassing the engine. The test passes; the production path still cannot produce such a score. The green test masks the dead feature.

### 5.2 `update_attacker` recomputation is O(sessions) per event

[persistence_service.py:273](backend/app/services/persistence_service.py:273) recomputes every session for an IP on every incoming event. Correct, but it degrades linearly with attacker session volume and will not meet a "real-time at scale" claim without incremental aggregation.

---

## 6. P1 — Reliability Findings

### 6.1 Unbounded in-memory growth

- `AsyncLogCollector._processed_event_ids` (set) — [log_collector.py:42](backend/app/services/log_collector.py:42).
- `SessionIntelligenceEngine._session_classifications` / `_session_profiles` (dicts) — `session_intelligence.py`.

All grow for the process lifetime with no eviction and no persistence-backed recovery. A long-running honeypot leaks memory; a restart silently drops session-intelligence state.

### 6.2 Startup re-ingest cost

`PIPELINE_FROM_BEGINNING: "true"` (`docker-compose.yml:39`) re-reads the full `cowrie.json` on every API restart. Idempotent (dedup via `event_id`), but adds unbounded startup cost as history grows.

### 6.3 Gemini timeout is configured but never enforced

`GEMINI_TIMEOUT=5.0` exists (`config.py:27`, `.env`), is stored on both Gemini services, and is **never passed to the SDK call**. A hung LLM request blocks the ingestion thread indefinitely. Because ingestion runs off the request loop (§3), the REST API stays up — but live ingestion halts.

---

## 7. Scientific Integrity Assessment (Directive §28)

### 7.1 The real numbers (read verbatim from `backend/app/ml/artifacts/metrics.json`)

| Metric | Value | Split |
|---|---|---|
| accuracy | **0.9449** | primary (same-template 80/20) |
| macro_f1 | 0.9229 | primary |
| macro_precision / recall | 0.9367 / 0.9158 | primary |
| weighted_f1 | 0.9436 | primary |
| **accuracy** | **0.6787** | **robustness (leave-families-out)** |
| **macro_f1** | **0.5267** | **robustness (leave-families-out)** |
| CV (LinearSVC / LogReg / ComplementNB) | 0.8539±0.018 / 0.8482 / 0.8146 | 5-fold |

Dataset: 1360 unique samples (1365 − 5 dups), 242 template families, class-imbalanced (EXECUTION 318 … PRIV_ESC 57). Weakest class: RECONNAISSANCE (F1 0.714). Environment recorded (Python 3.13.12 / sklearn 1.9.0 / numpy 2.5.2). `honesty_notes` present in the artifact.

### 7.2 There is no "99.89%" — and that is correct

**No file in the repository contains "99.89%".** The anti-fabrication constraint on that specific number was honored. The concern is *emphasis*, not fabrication: docs lead with 94.49% (optimistic, template-leaky) while the honest generalization figure (67.87%) — a 27-point drop — is the number a research reviewer would demand front-and-center.

### 7.3 Shipped evaluation artifacts contradict the prose

The per-sample evaluation CSVs record `classification_source` as **only ever `RULE` or `FALLBACK`** — the ML, HYBRID, and GEMINI paths never decided a labeled evaluation case. In the only run built to exercise Gemini, **Gemini succeeded 0/28**. Yet prose claims (e.g. "ML/HYBRID classified 21/21") assert otherwise. Additionally, "sub-millisecond ML path" is unsupported: measured non-rule latency is 200 ms–1.8 s, with **no hardware spec and no p50/p95/p99**. These are the most serious integrity gaps and must be reconciled (either fix the pipeline so ML/Gemini actually decide, or rewrite the claims to match reality).

### 7.4 Documentation drift

`pymongo` (synchronous) is used, but the paper/README reference "Motor (async MongoDB)." README/RUN say Python 3.12+; the Dockerfile uses 3.13-slim. Cosmetic vs. code, but a reviewer will notice.

---

## 8. Capability Gap Analysis (vs. an "intent-aware, predictive, robust" claim)

| Capability implied by framing | Present? | Evidence |
|---|---|---|
| KNOWN vs UNKNOWN / AMBIGUOUS / **novelty / OOD / abstention** | **No** | Classifier always returns one of 10 classes; no confidence-abstain, no OOD score. |
| **Predictive next-intent** (OBSERVED/INFERRED/PREDICTED) | **No** | `session_intelligence` tracks furthest stage in a fixed order; no prediction. |
| Real **stage-transition** modeling | **No** | Fixed `STAGE_ORDER`, no transition matrix / sequence model. |
| **Decomposable, explainable risk** | **Partial (good)** | `risk_engine` is additive & explainable — but event ceiling 65 breaks alerting (§5.1). |
| **Attacker profiling** | **Partial** | `update_attacker` aggregates per-IP, but O(n) per event (§5.2); no behavioral clustering. |
| **MITRE ATT&CK depth** | **Basic** | `mitre_mapper` maps to technique IDs (e.g. T1592); no sub-technique chains / coverage view. |
| **LLM prompt-injection hardening** | **Partial** | Schema + temp 0.1 (good); weak payload sanitization; timeout unenforced (§6.3). |
| **Adversarial robustness gate** | **Offline only** | `unseen_dataset.csv` (novel/low-conf/wrong-intent/benign) exists but gates nothing in CI. |
| **Latency percentiles / benchmarks** | **No** | `latency_results.csv` exists; no p50/p95/p99, no hardware, not in CI. |
| **Alert prioritization** | **N/A** | Alerts never fire (§5.1). |
| **MLOps / reproducibility** | **No** | Zero commits; mutable image tags; no hash-locking; no model registry/versioning. |
| **AuthN/AuthZ / TLS** | **No** | No auth on API/WS/Mongo; nginx is plain HTTP, no security headers. Mitigated only by loopback binding today. |

These are the substance of the roadmap: they are *additions*, not repairs, and each must ship with a measurable success criterion and a non-fabricated evaluation.

---

## 9. Reproducibility, MLOps & Deployment (infra sub-audit)

### 9.1 Reproducibility blockers
- Zero commits, repo rooted at `$HOME` (§2.2). **P0.**
- Image tags are mutable, not digest-pinned (`cowrie/cowrie:latest`, `nginx:alpine`, `node:20-alpine`, `python:3.13-slim`) → `docker compose up --build` is not byte-reproducible.
- Python deps are fully `==`-pinned (good) but **no hash-locking** and **no CVE scan** (`pip-audit`/`safety`) in any pipeline. Note: several pinned versions are future-dated relative to public advisory data and cannot be cross-checked here.

### 9.2 Container hardening gaps
- **Both containers run as root** (no `USER` directive in either Dockerfile). Biggest hardening gap.
- No `read_only` rootfs, no `cap_drop`, no `no-new-privileges`, no CPU/memory limits.
- Backend has a `HEALTHCHECK`; frontend has none (so `depends_on` can't gate on dashboard readiness).

### 9.3 Networking (mostly good)
- Every published host port is loopback-bound (`127.0.0.1:2222/8000/5173`); **MongoDB is not published**; API mounts honeypot logs **read-only** (`:ro`). Strong isolation.
- **CORS regex** `^https?://(localhost|127\.0\.0\.1)(:\d+)?$` with `allow_credentials=True` (`main.py:121-128`) allows *any* localhost port — broader than the explicit origins list; tighten before any non-local exposure.
- nginx (`frontend/nginx.conf`, 39 lines): correct REST + WS proxying; **missing** all security headers (CSP, X-Frame-Options, nosniff, Referrer-Policy, HSTS), no rate limiting, `server_tokens` not disabled, plain HTTP only.

---

## 10. Honeypot Host-Safety (Directive §15) — VERIFIED SAFE

**Verdict: there is no path by which attacker-supplied commands execute on the host or backend.** Independently confirmed by direct reads plus the infra sub-audit:

- **Emulated shell, not a real backend.** `honeypot/etc/cowrie.cfg` is the stock upstream dist file ("DO NOT EDIT THIS FILE!"). Decisive: `backend = shell` ([cowrie.cfg:110](honeypot/etc/cowrie.cfg:110)) — Cowrie's *emulated* Python shell, **not** `proxy`/`pool`. The `[proxy]`/`[backend_pool]` `backend_user=root`/`backend_pass=root` values are **inert** because `backend = shell`.
- **Loopback-only listener.** `[ssh] listen_endpoints = tcp:2222:interface=127.0.0.1` ([cowrie.cfg:758](honeypot/etc/cowrie.cfg:758)); `[telnet] enabled = false` ([cowrie.cfg:827](honeypot/etc/cowrie.cfg:827)). Compose additionally binds `127.0.0.1:2222` — double-restricted.
- **Read-only file-tail ingestion.** The API mounts `cowrie-logs:/cowrie:ro` (`docker-compose.yml:43`); `log_collector.py` opens the log `"rb"` and only *parses* lines into Pydantic objects. No socket, pipe, or shell in the ingestion path.
- **No execution primitives in ingestion/classification.** A scan of `backend/app/services/` for `os.system|subprocess|eval(|exec(|popen|Popen|shell=True` matches **only** the regex *detection signatures* in `rule_classifier.py:110,115` — string literals used to classify payloads, never invoked.
- **`userdb.txt` weak creds are intentional bait.** `root/root`, `admin/admin`, `guest/guest`, `root/password`, `root/123456`, `admin/password` (`honeypot/etc/userdb.txt`) — deliberate deception surface, correct for a honeypot.
- **Data sanitization before persistence.** Passwords are redacted to `[REDACTED]` before storage (`test_persistence_service.py` asserts `saved["raw_event"]["password"] == "[REDACTED]"`; WS test asserts `"password" not in received`).

This is a genuine strength and satisfies the §15 mandate.

---

## 11. Test Suite Assessment (test sub-audit)

- **74 tests, 74 pass, 0 skip/xfail, ~16.7 s.** Fully hermetic: `mongomock` for Mongo, `MagicMock`/`enabled=False` for Gemini, `tempfile` for the collector, Starlette `TestClient` for API/WS. No live Mongo or network needed.
- **Strong assertions** throughout (exact arithmetic, status codes, mock-call counts, redaction) — not `is not None` filler.
- **Gaps:**
  - **Entire ML stack untested** (`intent_ml_classifier`, `train`, `dataset`, `split`, `labels`); a real `.joblib` artifact ships but nothing loads it in pytest — hybrid tests use `_StubML`.
  - ML-regression, load/latency, and adversarial/unseen evaluation are **offline scripts/CSVs only** — they gate nothing.
  - Thin coverage: e2e (1 happy path), `session_intelligence` (1 test), `gemini_session_analyst` (disabled path only), pipeline orchestration largely unexercised.
  - No security tests beyond redaction (no auth/injection/CORS/fuzz). `GET /api/events/recent` untested.
  - The alert test (§5.1 note) passes only because it constructs the score directly, masking the dead production path.

---

## 12. Prioritized Findings Register

| ID | Pri | Finding | Primary evidence | Fix class |
|---|---|---|---|---|
| F1 | **P0** | Alert subsystem unreachable (event risk ≤65 vs ≥75 gates) | pipeline.py:127, persistence_service.py:102, models/database.py:107, risk_engine.py | Repair |
| F2 | **P0** | Honest generalization accuracy (67.87%) buried under template-leaky 94.49% | metrics.json | Docs + eval |
| F3 | **P0** | Eval CSVs contradict prose (ML/Gemini never decided; Gemini 0/28; no latency percentiles) | evaluation CSVs, docs | Repair + docs |
| F4 | **P0** | No git history; repo rooted at `$HOME` | git queries | Process |
| F5 | **P1** | `GEMINI_TIMEOUT` never enforced → ingestion can hang | gemini_classifier.py:65,156 | Repair |
| F6 | **P1** | Unbounded in-memory growth (`_processed_event_ids`, session dicts); state lost on restart | log_collector.py:42, session_intelligence.py | Repair |
| F7 | **P1** | `update_attacker` O(sessions) per event | persistence_service.py:273 | Perf |
| F8 | **P1** | No novelty/OOD/abstention; no predictive next-intent; no transition modeling | intent_ml_classifier.py, session_intelligence.py | Feature |
| F9 | **P1** | No auth/TLS anywhere; nginx missing security headers; CORS allows any localhost port | main.py:121, nginx.conf | Hardening |
| F10 | **P2** | ML stack untested; adversarial/load/regression offline-only | test sub-audit | Tests |
| F11 | **P2** | Containers run as root; mutable image tags; no hash-lock/CVE scan | Dockerfiles, requirements | Hardening |
| F12 | **P2** | Weak Gemini payload sanitization; session analyst lacks response_schema | gemini_classifier.py:101, gemini_session_analyst.py | Repair |
| F13 | **P3** | Misleading frontend fallbacks (null IP→127.0.0.1, missing proto→SSH) | frontend sub-audit | Repair |
| F14 | **P3** | Doc drift (Motor vs pymongo; Python 3.12 vs 3.13) | docs, Dockerfile | Docs |
| F15 | **P3** | `GET /api/events/recent` untested | events.py:60 | Tests |

---

## 13. Overall Verdict

INT-AWARE is **not fake** — it is a working, safely-isolated honeypot-analytics pipeline with real ML artifacts, real database aggregations, a fabrication-free frontend, and a hermetic test suite. Its shortfall against a research-grade bar is threefold: **(1) a broken alerting path** that no test catches; **(2) integrity gaps** where documentation outruns the evidence (optimistic accuracy framing; prose that the shipped CSVs contradict); and **(3) missing "intelligence"** — the novelty, prediction, robustness, and observability capabilities that would justify the "intent-aware, predictive" framing do not yet exist.

Every one of these is addressable without fabricating anything. The remediation sequence — repair correctness (P0) before hardening and features — is specified in the accompanying `ROADMAP.md`.

*Prepared read-only. No code was modified in producing this audit.*
