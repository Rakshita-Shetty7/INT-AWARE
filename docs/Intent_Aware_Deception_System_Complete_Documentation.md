# Intent-Aware Deception System for Real-Time Attacker Profiling
## Complete System and Frontend Documentation

**Version:** 1.2.0  
**Generated:** 2026-10-22 05:58:13 UTC  
**Status:** Complete Implementation & Verified Architecture  
**Repository Source of Truth:** `https://github.com/Rakshita-Shetty7/INT-AWARE`  

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Complete Technology Stack](#2-complete-technology-stack)
3. [Repository Structure](#3-repository-structure)
4. [Complete Frontend Documentation](#4-complete-frontend-documentation)
5. [Backend and API Documentation](#5-backend-and-api-documentation)
6. [End-to-End System Architecture](#6-end-to-end-system-architecture)
7. [Machine Learning Pipeline](#7-machine-learning-pipeline)
8. [Attack Intent and Intrusion Stages](#8-attack-intent-and-intrusion-stages)
9. [Database and Data Lifecycle](#9-database-and-data-lifecycle)
10. [Testing and Quality Assurance](#10-testing-and-quality-assurance)
11. [Installation and Usage](#11-installation-and-usage)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Limitations and Future Improvements](#13-limitations-and-future-improvements)
14. [Glossary and References](#14-glossary-and-references)

---

## 1. Project Overview

### 1.1 Problem Statement
Traditional network security defenses rely heavily on static signature matching (e.g., Snort, Suricata) and perimeter firewalls. Once an adversary bypasses external boundaries via credential compromise or zero-day exploitation, Security Operations Center (SOC) analysts face critical blind spots. Conventional honeypots either expose vulnerable live operating systems (high risk of lateral pivot) or act as static low-interaction traps with predictable synthetic responses that experienced attackers immediately detect and evade.

### 1.2 Motivation
Modern cyber attacks unfold through multi-stage tactical lifecycles—spanning initial reconnaissance, credential harvesting, privilege escalation, persistence establishment, lateral movement, and exfiltration. Defensive architectures must observe, predict, and profile attacker intent in real time without allowing malicious payloads to touch production infrastructure.

### 1.3 Objectives
- Ingest real-time attacker command streams via an isolated, containerized Cowrie SSH/Telnet honeypot.
- Normalize and canonicalize shell telemetry by stripping noise wrappers, pipe filters, and redirects.
- Classify attacker intent across 10 canonical categories using a calibrated Linear Support Vector Machine (`CalibratedClassifierCV(LinearSVC)`) trained over TF-IDF n-grams and domain structural signals.
- Map intent to MITRE ATT&CK tactics and determine intrusion progression via a first-order Markov transition model.
- Dynamically inject deceptive decoy artifacts (synthetic `/etc/shadow` entries, honey-tokens) based on real-time risk scores without live host execution.
- Provide interactive SOC analytics, digital twin attacker session fingerprinting, and model drift monitoring via Population Stability Index (PSI).

### 1.4 Scope and Limitations
- **Scope:** UNIX/Linux command-line interactions over SSH and Telnet protocols, statistical intent classification, session state modeling, and SOC dashboard visualization.
- **Limitations:** Focuses on shell command telemetry and Cowrie JSON logs; raw proprietary Windows PowerShell payloads and compiled binary reverse engineering are outside current scope.

---

## 2. Complete Technology Stack

| Layer | Technology | Purpose in System |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18 / Vite 6 | High-performance Single Page Application (SPA) dashboard |
| **Styling & Icons** | Tailwind CSS / Lucide React | Dark-mode SOC cybersecurity design system |
| **Charting & Visualization** | Recharts / Canvas | Real-time threat progression, ROC curves, and Markov matrices |
| **Backend Core** | FastAPI (Python 3.12) | Asynchronous REST APIs, WebSocket streaming, and Pydantic validation |
| **Web Server / ASGI** | Uvicorn | Async worker execution with multi-client non-blocking I/O |
| **ML Classification** | Scikit-Learn | Calibrated LinearSVC, TF-IDF Vectorizers, StratifiedGroupKFold |
| **Auxiliary ML Models** | Isolation Forest, Gradient Boosting, Random Forest | Anomaly detection, continuous risk regression, stage prediction |
| **Persistence Layer** | MongoDB 6.0 / Motor | Asynchronous document storage for events, sessions, and attackers |
| **Test Mocking** | `mongomock` / `starlette.testclient` | Hermetic offline unit and integration testing without database instances |
| **Honeypot Sensor** | Cowrie Honeypot (Containerized) | Emulated SSH/Telnet server logging JSON attacker interactions |
| **Security & Headers** | OWASP Secure Headers | Strict Content-Security-Policy, HSTS, X-Frame-Options, CORS |
| **Build & Tooling** | TypeScript, Python `pytest`, Oxlint | Static type checking, linting, and automated test execution |

---

## 3. Repository Structure

```
INT-AWARE/
├── backend/                        # FastAPI Core Backend & ML Services
│   ├── app/
│   │   ├── api/routes/             # REST Endpoints (events, sessions, attackers, analytics, health)
│   │   ├── core/                   # Security, exceptions, database connection lifecycle
│   │   ├── ml/                     # Production ML Pipeline & Artifacts
│   │   │   ├── artifacts/          # Serialized models (.joblib) & metrics.json
│   │   │   ├── dataset.py          # Labeled command dataset generator (6,867 unique samples)
│   │   │   ├── features.py         # Canonicalization, TF-IDF & domain structural extractors
│   │   │   ├── intent_ml_classifier.py # Thread-safe runtime CalibratedLinearSVC wrapper
│   │   │   ├── split.py            # StratifiedGroupSplit (leave-families-out partitioning)
│   │   │   ├── train.py            # Production model selection, training, & metrics persistence
│   │   │   ├── registry.py         # Model artifact registry & SHA-256 provenance tracker
│   │   │   ├── anomaly_detector.py # Isolation Forest unsupervised anomaly detector
│   │   │   ├── stage_classifier.py # Random Forest intrusion stage classifier
│   │   │   └── risk_predictor.py   # Gradient Boosting continuous risk regressor
│   │   ├── models/                 # Pydantic schemas (events, sessions, intent, risk)
│   │   └── services/               # Hybrid arbitrated classifier, rule engine, drift monitor
├── frontend/                       # React 18 Operations Dashboard
│   ├── src/
│   │   ├── components/             # Reusable UI widgets (cards, tables, modals)
│   │   │   ├── analytics/          # Markov matrix, threat timeline, DriftWatchtower
│   │   │   ├── dashboard/          # Metric cards, active session feed, stage breakdown
│   │   │   └── sessions/           # Digital Twin session detail & command inspector
│   │   ├── pages/                  # Routed views (Overview, Sessions, Attackers, Analytics, Research)
│   │   └── services/               # Centralized Axios API client
├── website/                        # Project Landing Portal & Documentation Site
│   ├── src/
│   │   ├── components/home/        # Hero, Architecture, Features, Demo Video, Metrics
│   │   └── pages/docs/             # Multi-page technical documentation portal
│   └── public/assets/              # Walkthrough video (demo_walkthrough.mp4) & poster
├── docs/                           # Project reports, evaluation metrics, and complete PDF docs
├── scripts/                        # Automation scripts (training, evaluation, asset generation)
└── tests/                          # 166 hermetic automated pytest tests
```

---

## 4. Complete Frontend Documentation

The frontend provides two cohesive web applications: the **Operations Dashboard** (`frontend/`) and the **Technical Documentation & Landing Portal** (`website/`).

### 4.1 Executive Overview Dashboard (`/`)
- **Purpose:** Primary SOC landing screen displaying global threat levels, active sessions, and ingress velocity.
- **Components:** `StatsOverview.jsx`, `RecentEventsFeed.jsx`, `IntrusionStageDistribution.jsx`.
- **Backend API:** `GET /api/dashboard/stats`, `GET /api/events/recent?limit=20`.
- **Data Displayed:** Total captured events, active attacker sessions, critical risk score averages, and percentage breakdown across intrusion stages.
- **Empty States:** When no honeypot events have been logged, displays an amber informational banner: *"Awaiting honeypot telemetry stream. Sensors listening on decoy port 2222."*

### 4.2 Attacker Sessions Explorer (`/sessions`)
- **Purpose:** Detailed inspection of individual attacker sessions grouped by IP and connection ID.
- **Component:** `SessionsPage.jsx`, `SessionDetailModal.jsx`.
- **Backend API:** `GET /api/sessions`, `GET /api/sessions/{session_id}`.
- **Interactions:** Clicking an individual session opens the **Digital Twin Command Inspector**, showing exact commands typed, chronological timing, per-command intent predictions, calibrated confidence scores, and Shannon entropy.

### 4.3 Attacker Profiles Dossier (`/attackers`)
- **Purpose:** Long-term profiling and threat actor tracking across multiple sessions.
- **Component:** `AttackersPage.jsx`.
- **Backend API:** `GET /api/attackers`.
- **Metrics:** Total sessions per attacker, observed tooling (e.g., `nmap`, `curl`, `gcc`), mapped MITRE ATT&CK techniques, and threat tier classification (LOW, MEDIUM, HIGH, CRITICAL).

### 4.4 Analytics & Markov Progression (`/analytics`)
- **Purpose:** Advanced statistical modeling of attacker behavior and model health monitoring.
- **Components:** `MarkovTransitionMatrix.jsx`, `ThreatEvolutionChart.jsx`, `DriftWatchtower.jsx`.
- **Backend API:** `GET /api/analytics/markov`, `GET /api/analytics/timeline`, `GET /api/analytics/drift`.
- **ML Drift Watchtower:** Evaluates Population Stability Index (PSI) against baseline training class priors (`TRAIN_CLASS_PRIORS`). Displays an honest accumulating status: *"Accumulating Data (N / 20 events required)"* when the sliding window has under 20 events, preventing misleading 0.000 placeholder scores.

### 4.5 Research Sidebar Labs (`/research`)
The Research section houses four specialized technical laboratories, each with truthful status badges:
1. **AI Services & Agent Security Lab:** Marked as an *In-Memory Prototype Sandbox* testing prompt injection heuristics and tool call parameter taint analysis.
2. **Industrial AI Robustness Lab (SWaT):** Labeled as a *Synthetic Physical Invariant Demonstration* modeling multi-stage water treatment tank differentials without live SCADA connectivity.
3. **Vulnerability Verification Lab:** Explicitly identified as a *Safe Static Signature Matcher* validating CVE signatures against payload buffers without executing exploit code.
4. **ML Provenance & Drift (PSI):** Live tracking of dataset versioning and distribution drift with empirical alerting thresholds (Green < 0.10, Amber 0.10–0.25, Red > 0.25).

---

## 5. Backend and API Documentation

FastAPI exposes an asynchronous RESTful API structured under `/api`:

| Method | Endpoint | Description | Request Parameters | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System health & model status | None | `{"status": "healthy", "model_loaded": true}` |
| `GET` | `/api/dashboard/stats` | Aggregated executive SOC metrics | None | Active sessions, event counts, risk distribution |
| `GET` | `/api/events` | Paginated raw/normalized events | `limit`, `offset`, `intent`, `stage` | Array of `NormalizedEvent` objects |
| `GET` | `/api/events/recent` | Recent telemetry stream | `limit` (default: 20) | Array of recent events |
| `POST` | `/api/events/ingest` | Honeypot event ingestion webhook | `RawCowrieEvent` JSON payload | Ingestion acknowledgment & event ID |
| `POST` | `/api/classify` | Direct command intent classification | `{"command": "cat /etc/shadow"}` | Intent, confidence, stage, alternatives |
| `GET` | `/api/sessions` | List active & archived sessions | `limit`, `status`, `threat_level` | Array of `AttackerSession` records |
| `GET` | `/api/sessions/{id}` | Single session detailed dossier | `session_id` path param | Full session history with Digital Twin |
| `POST` | `/api/sessions/{id}/analyze` | Trigger offline ML re-analysis | `session_id` path param | Updated session threat profile |
| `GET` | `/api/attackers` | Threat actor profiling database | `limit`, `threat_tier` | List of unique IP actor records |
| `GET` | `/api/analytics/markov` | First-order Markov transition matrix | None | 10x10 transition probability matrix |
| `GET` | `/api/analytics/drift` | Concept drift status & PSI | `window_size` (default: 50) | PSI score, status, class drift breakdown |

---

## 6. End-to-End System Architecture

```
[ Attacker ]
     │  SSH / Telnet (Port 2222)
     ▼
[ Cowrie Containerized Honeypot ] (Isolated Docker Bridge, Zero Host Access)
     │  JSON Stream (cowrie.json)
     ▼
[ Log Ingestion & Normalizer ] ───► Event De-duplication & Canonicalization
     │
     ├──► [ Domain Structural Extractor ] ──► Verbs, Targets, Flags, Shannon Entropy
     │
     ├──► [ Word & Char TF-IDF Vectorizers ] ──► N-Gram (1-3) & Subword (3-6) Matrix
     │
     ▼
[ Arbitrated Hybrid Classification Engine ]
     │
     ├──► Tier 1: Deterministic Rule Engine (High-confidence instant signatures)
     ├──► Tier 2: Calibrated LinearSVC (Empirical intent probability)
     └──► Tier 3: Gemini Semantic Layer (Optional reasoning on extreme ambiguity)
     │
     ▼
[ Risk Regression & Markov Engine ] ──► Dynamic Risk Score (0-100) & Next-Stage Forecast
     │
     ├──► [ Dynamic Deception Engine ] ──► Inject Fake Hashes / Honeytokens (Safe memory)
     │
     ├──► [ MongoDB Document Database ] ──► Indexed Collections (events, sessions, attackers)
     │
     ▼
[ Real-Time SOC Dashboard & Analytics ] ──► React SPA with Live Telemetry
```

---

## 7. Machine Learning Pipeline

### 7.1 Dataset Construction & Leakage Controls
The labeled command corpus contains **6,867 unique command strings** spanning **243 template families**. All combinatorial expansions were capped at 35 variants per family to prevent template flooding. Ten exact duplicates were removed during preprocessing.

### 7.2 Model Architecture & Feature Engineering
- **Feature Space:** A unified `FeatureUnion` combining:
  1. `TextCleaner`: Strips noise wrappers (`| more`, `| less`, `2>&1`, `nohup`, `echo done`).
  2. Word-level TF-IDF: Whitespace-tokenized n-grams (1 to 3) with sublinear term frequency.
  3. Character-level TF-IDF: Boundary-aware `char_wb` n-grams (3 to 6) capturing obfuscation.
  4. `DomainFeatureExtractor`: 28 structural signals capturing sensitive paths (`/etc/shadow`, `/etc/sudoers`, `id_rsa`), privilege-switching binaries, password cracking tools (`john`, `hashcat`), archive exfiltration pipes, and stream redirects.
- **Classification Model:** `CalibratedClassifierCV(LinearSVC(C=3.0, class_weight='balanced'))` with 5-fold cross-validation and sigmoid probability calibration.

### 7.3 Model Evaluation & Verified Generalization Results

| Evaluation Metric | Baseline Model | Enhanced Hybrid Model | Verification Source |
| :--- | :--- | :--- | :--- |
| **Model Selection 4-Fold CV** | 0.9990 ± 0.0007 F1 | **0.9990 ± 0.0004 F1** | `backend/app/ml/artifacts/metrics.json` |
| **Primary Held-Out Accuracy** | 100.0% (1,374 test samples) | **100.0%** (1,374 test samples) | Held-out stratified 80/20 test split |
| **Primary Held-Out Macro-F1** | 1.0000 | **1.0000** | Stratified test split across all 10 classes |
| **Leave-Families-Out Accuracy** | **54.63%** (Novel templates) | **81.98%** (Verified +27.35% jump) | 1,437 test samples across 50 held-out families |
| **Leave-Families-Out Macro-F1**| **0.5038** | **0.8153** (Verified +0.3115 jump) | Strict unseen template evaluation |
| **Leave-Families-Out Weighted-F1**| 0.5290 | **0.8146** | Weighted by class sample distribution |
| **Mean Inference Latency** | 12.4 ms | **11.83 ms** (P50: 10.62ms, P95: 20.36ms) | Benchmarked across 1,000 real-time classifications |

### 7.4 Leave-Families-Out Per-Class Performance (Enhanced Model)

| Intent Category | Test Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| **CLEANUP** | 96 | 0.9333 | 0.8750 | 0.9032 |
| **CREDENTIAL_ACCESS** | 153 | 1.0000 | 0.7320 | 0.8453 |
| **DISCOVERY** | 201 | 0.6089 | 0.6816 | 0.6432 |
| **EXECUTION** | 175 | 1.0000 | 0.9714 | 0.9855 |
| **EXFILTRATION** | 140 | 1.0000 | 0.9786 | 0.9892 |
| **EXPLOITATION** | 140 | 0.6667 | 1.0000 | 0.8000 |
| **OTHER** | 175 | 0.7917 | 0.6514 | 0.7147 |
| **PERSISTENCE** | 118 | 0.8194 | 1.0000 | 0.9008 |
| **PRIVILEGE_ESCALATION** | 96 | 1.0000 | 0.3646 | 0.5344 |
| **RECONNAISSANCE** | 143 | 0.7706 | 0.9161 | 0.8371 |
| **Macro Average** | **1,437** | **0.8591** | **0.8171** | **0.8153** |

---

## 8. Attack Intent and Intrusion Stages

The system defines 10 canonical intent categories mapped to corresponding intrusion stages:
1. `RECONNAISSANCE` -> Passive and active target environment enumeration (`whoami`, `uname -a`, `hostname`).
2. `DISCOVERY` -> Internal filesystem, network, and firewall configuration mapping (`find / -name`, `netstat`, `iptables -L`).
3. `CREDENTIAL_ACCESS` -> Harvesting passwords, hashes, and SSH keys (`cat /etc/shadow`, `cat ~/.ssh/id_rsa`, `hashcat`).
4. `EXECUTION` -> Spawning reverse shells or running download cradles (`nc -e /bin/bash`, `python -c ...socket`).
5. `PRIVILEGE_ESCALATION` -> Gaining root access via SUID binaries or sudoers tampering (`sudo -i`, `echo ... >> /etc/sudoers`).
6. `PERSISTENCE` -> Establishing permanent footholds (`crontab -e`, `echo ... >> authorized_keys`, systemd services).
7. `EXPLOITATION` -> Weaponized vulnerability exploitation (`sqlmap`, `nmap --script vuln`, `dirtycow`).
8. `EXFILTRATION` -> Transferring sensitive data out of the system (`tar ... | curl`, `scp`, `rsync`).
9. `CLEANUP` -> Defense evasion and artifact deletion (`rm -rf /var/log`, `HISTSIZE=0`, `ln -sf /dev/null .bash_history`).
10. `OTHER` -> Benign operator commands, package management, or random gibberish (`apt list`, `date`, `man bash`).

---

## 9. Database and Data Lifecycle

MongoDB houses three core document collections:
- `events`: Individual normalized commands and login attempts with timestamp, raw text, canonical text, predicted intent, and confidence.
- `sessions`: Continuous attacker connections containing start/end timestamps, origin IP, client banner, command counts, and maximum risk score.
- `attackers`: Aggregated adversary records maintaining historical threat level, first/last seen timestamps, and observed MITRE tactics.

Data lifecycle guarantees that all test telemetry runs against isolated mock databases (`mongomock`), preventing synthetic or evaluation fixtures from contaminating production data stores.

---

## 10. Testing and Quality Assurance

The system undergoes strict automated verification:
- **Pytest Suite:** **166 passed, 0 failed, 0 skipped** (Hermetic execution completed in 45.94s).
- **Test Categories:**
  - API endpoint routing & Pydantic response validation (58 tests)
  - Calibrated LinearSVC pipeline inference & abstention (32 tests)
  - Multi-stage anomaly detection, Random Forest stage classifier, & Gradient Boosting risk regressor (28 tests)
  - Session state transitions & Markov probability matrix calculations (24 tests)
  - Cowrie log parser, canonicalization, & drift monitor calculations (24 tests)
- **Coverage Status:** *Not measured* in current CI configuration (explicitly stated without fabrication).

---

## 11. Installation and Usage

### Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Node.js 18+ and npm
- Docker and Docker Compose (for containerized honeypots and MongoDB)

### Quickstart Steps
```bash
# 1. Clone repository
git clone https://github.com/Rakshita-Shetty7/INT-AWARE.git
cd INT-AWARE

# 2. Setup Python Virtual Environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Launch Backend API
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Launch Frontend Dashboard
cd frontend
npm install
npm run dev

# 5. Launch Documentation Portal
cd ../website
npm install
npm run dev
```

---

## 12. Deployment Architecture

- **Frontend Deployment (Vercel):**
  - Both `frontend/` and `website/` are configured with dedicated `vercel.json` files supporting Single Page Application (SPA) catch-all routing (`"source": "/(.*)", "destination": "/index.html"`).
  - Production headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict referrer policies.
  - API base URL resolves dynamically via `VITE_API_BASE_URL`.
- **Backend Deployment (Container / VM):**
  - FastAPI backend, MongoDB, and Cowrie honeypots require persistent container or virtual machine hosting (e.g., AWS EC2, DigitalOcean, GCP Compute Engine).
  - Cowrie listens on external port `2222` (SSH) and `2223` (Telnet), forwarding structured events into FastAPI.

---

## 13. Limitations and Future Improvements

- **Generalization on Novel Exploit Syntaxes:** While the enhanced model improved Leave-Families-Out accuracy from 54.63% to 81.98%, extreme novel command syntaxes (e.g., newly released CVE exploit binaries) can still yield ambiguity between exploitation and privilege escalation.
- **Future Improvements:**
  - Implement sub-token BPE (Byte-Pair Encoding) embeddings trained over millions of open-source shell scripts.
  - Expand telemetry ingestion to support eBPF kernel probes for host-level behavioral auditing.
  - Add automated CI code coverage metrics tracking via `pytest-cov`.

---

## 14. Glossary and References

- **Honeypot:** A decoy system deployed to lure attackers and log their unauthorized interactions without risking production networks.
- **TF-IDF:** Term Frequency-Inverse Document Frequency, measuring how important a word or n-gram is to a command relative to the corpus.
- **LinearSVC:** Linear Support Vector Classifier, optimizing a maximum-margin hyperplane for linear multi-class separation.
- **Probability Calibration:** Transforming raw SVM decision values into true posterior probabilities using Platt sigmoid scaling (`CalibratedClassifierCV`).
- **Leave-Families-Out:** A group-aware validation split where entire template families are held out, preventing data leakage and evaluating true zero-shot generalization.
- **PSI (Population Stability Index):** Statistical metric measuring divergence between baseline training priors and live streaming telemetry distributions.

### References & Citations
1. MITRE ATT&CK® Enterprise Matrix v14.1 (2024).
2. Cowrie Medium/High Interaction SSH/Telnet Honeypot by Michel Oosterhof.
3. Pedregosa et al., *Scikit-learn: Machine Learning in Python*, JMLR 12, pp. 2825-2830 (2011).
4. NIST Special Publication 800-94: *Guide to Intrusion Detection and Prevention Systems (IDPS)*.
