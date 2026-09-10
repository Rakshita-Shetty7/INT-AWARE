# Dashboard Guide — Every Section, Term & Why It Exists
## Intent-Aware Deception System for Real-Time Attacker Profiling

> **What this document is.** A complete, screen-by-screen walkthrough of the analyst
> dashboard: every page, every panel, every chart, every badge, every term — and *why each
> one is there*. It is written so you can (a) explain any element in a viva, and (b) paste
> descriptions straight into your report.
>
> **Stack:** Vite + React 19 + React Router + Recharts + Tailwind CSS + lucide-react icons.
> The dashboard is a read-only *analyst console* — it never sends commands to the honeypot; it
> only visualises what the backend pipeline has already classified and scored.
>
> **How data reaches the screen.** Every page fetches from the FastAPI backend over
> `GET /api/*`. The **Overview** page and the **top navigation bar** additionally hold open
> two **WebSocket** connections (`/ws/events`, `/ws/alerts`) so new attacks appear live,
> **without a page refresh**.

---

## 0. Vocabulary — the core terms first

These terms recur on every screen. Understand these seven and the whole dashboard reads
clearly.

| Term | Plain meaning | Why the system uses it |
| :-- | :-- | :-- |
| **Session** | One connection from an attacker to the honeypot, from login to disconnect. | The unit we profile — intent and risk are computed *per session*. |
| **Event** | One single action inside a session (one command typed, one login attempt). | The atomic unit the ML model classifies. A session is a sequence of events. |
| **Attacker** | A distinct source IP address, aggregated across all its sessions. | Lets us profile a *host* over time, not just one connection. |
| **Intent** | The attacker's *goal* behind a command (one of 10 MITRE-aligned classes). | The core research contribution — we infer *why*, not just *what*. |
| **Attack stage** | Where the action sits in the attack lifecycle (kill-chain position). | Turns isolated commands into a *progression* story. |
| **Risk score** | A number 0–100 rating how dangerous a session is. | A single, explainable severity signal an analyst can triage on. |
| **Classification source** | Which engine decided the intent: `RULE`, `ML`, `HYBRID`, `GEMINI`, or `FALLBACK`. | Transparency — every decision is auditable, never a black box. |

The 10 **intent classes** (used everywhere, always in this order of escalation):
`RECONNAISSANCE → DISCOVERY → CREDENTIAL_ACCESS → EXECUTION → PRIVILEGE_ESCALATION →
PERSISTENCE → EXPLOITATION → EXFILTRATION → CLEANUP → OTHER`.

The 4 **severity tiers** (derived from the risk score):
**LOW** (0–24) · **MEDIUM** (25–49) · **HIGH** (50–74) · **CRITICAL** (75–100, raises an alert).

---

## 1. Global layout (present on every page)

The app shell is: a fixed **top navbar**, a left **sidebar**, and the page content area.
Page background `#0a0d14` (near-black navy) — a dark "security operations centre" theme
chosen for long analyst viewing sessions and to make the coloured risk/intent signals pop.

### 1.1 Top Navbar

- **Left:** a cyan `Shield` icon + the product title **"Intent-Aware Deception System"** and
  subtitle **"REAL-TIME ATTACKER PROFILING & HONEYPOT TELEMETRY"**.
- **Centre-right:** a live **UTC system clock** (updates every second) — analysts standardise
  on UTC so timestamps are unambiguous across time zones.
- **Right: five live status badges.** These are the system's "vital signs", refreshed by
  polling `GET /api/health` every 15 seconds. Each answers one operational question:

| Badge | States (exact text) | What it tells you | Why it matters |
| :-- | :-- | :-- | :-- |
| **Live stream** | `LIVE STREAM` / `CONNECTING...` / `DISCONNECTED` | Whether the `/ws/events` WebSocket is connected (green pulsing dot / amber / red) | Confirms you are seeing events in real time, not stale data |
| **Database** | `DB: OK` / `DB: ERR` | Whether MongoDB is reachable (`database === 'connected'`) | If the DB is down, nothing persists |
| **ML model** | `ML: {N}%` / `ML: ON` / `ML: OFF` | Whether the ML classifier loaded, and its held-out accuracy | Proves the ML core is live; hover shows model name + class count + accuracy |
| **AI / Gemini** | `AI: ON` / `AI: OFF` | Whether the optional Gemini layer is configured | Honestly shows the LLM is *optional* — `OFF` still means fully operational |
| **Honeypot feed** | `HONEYPOT: FEED` / `HONEYPOT: IDLE` | Whether the Cowrie log file is present and being read | Confirms the capture source is connected |

> **Why these five and not a generic "online" light:** each maps to one independently-failing
> subsystem (capture → storage → ML → AI → stream). An analyst can see *exactly* which layer is
> degraded at a glance. Note the ML and AI badges are deliberately separate — the design
> principle "ML is mandatory, Gemini is optional" is made visible right in the header.

### 1.2 Left Sidebar

Section label **"Security Operations"**, then five navigation links. The active page is
highlighted cyan.

| Label | Route | Icon | What it opens |
| :-- | :-- | :-- | :-- |
| **Overview** | `/` | dashboard grid | The live KPI + charts home page |
| **Live Sessions** | `/sessions` | radio | The searchable list of all sessions |
| **Attacker Profiles** | `/attackers` | users | Per-source-IP aggregated profiles |
| **Threat Alerts** | `/alerts` | alert-octagon | CRITICAL-risk alerts |
| **Analytics** | `/analytics` | bar-chart | Cross-dimensional charts |

Sidebar footer: a link **"FastAPI OpenAPI Docs"** (opens `/docs` — the live API explorer) and
the caption "Vite + React 19 + Tailwind CSS".

---

## 2. Page — Overview (`/`)

The home page. Its job: answer *"what is happening right now?"* in one screen. It opens on a
row of KPI cards, then telemetry panels. This is the only page (besides the navbar) that
consumes **live WebSockets**, so numbers and rows here update on their own.

### 2.1 KPI stat cards (row of six)

Each is a big number from `GET /api/dashboard/stats`. Visual order:

| # | Title | Subtitle (the exact definition shown) | What it counts | Why it's a top-line KPI |
| :-- | :-- | :-- | :-- | :-- |
| 1 | **Total Sessions** | "Honeypot connections" | All sessions ever captured | Overall engagement volume |
| 2 | **Active Sessions** | "Live connections" | Sessions not yet closed | What's happening *now* |
| 3 | **Total Attackers** | "Distinct source IPs" | Unique attacker IPs | How many distinct hosts |
| 4 | **Total Events** | "Analyzed actions" | Every classified action | Total workload processed (ticks up live) |
| 5 | **High Risk** | "Risk 50–74" | Sessions in the HIGH tier | Serious-but-not-critical queue |
| 6 | **Critical Alerts** | "Risk >= 75" | Open CRITICAL alerts | The "drop everything" count (ticks up live) |

> **Live behaviour:** each `/ws/events` message increments **Total Events**; each `/ws/alerts`
> message increments **Critical Alerts**. You literally watch the counters move as you attack.

### 2.2 Panels

**Row A**
1. **Attack Telemetry Timeline** — sub *"Events & active sessions volume"*. An area chart of
   event volume and session volume over time. *Why:* shows bursts of activity — a spike is a
   concentrated attack.
2. **Intent Distribution** — sub *"Classified attacker goals"*. A donut of the 10 intents.
   *Why:* the at-a-glance answer to "what are attackers mostly trying to do?"

**Row B**
3. **Threat Severity Tiers** — sub *"Evaluated session risk levels"*. Bar chart of
   LOW/MEDIUM/HIGH/CRITICAL counts. *Why:* the shape of your threat queue.
4. **High Risk Alerts** — sub *"Threshold: Risk Score ≥ 75"*. The five most recent CRITICAL
   alerts (`GET /api/alerts?limit=5`). *Why:* immediate triage list.
5. **Live Ingested Telemetry** — sub *"Streaming real-time actions"*. The eight newest events
   (`GET /api/events/recent?limit=8`), each with intent, severity, and a **source badge**.
   *Why:* the live "tail -f" of the honeypot — this is where you watch each attack land.

---

## 3. Page — Live Sessions (`/sessions`)

Heading **"Live & Historical Attacker Sessions"**, sub *"Total Captured Sessions: {N}"*.
A searchable, paginated table of every session. *Why this page exists:* the Overview shows
aggregates; this is where you drill into individual connections.

### 3.1 Filter toolbar

| Filter | Options | API param | Why |
| :-- | :-- | :-- | :-- |
| **Attacker IP** | free text (e.g. `192.168.1.100`) | `source_ip` | Find all sessions from one host |
| **Risk Severity** | All / LOW / MEDIUM / HIGH / CRITICAL | `severity` | Triage by danger |
| **Dominant Intent** | All / the 10 intents | `intent` | Hunt a specific behaviour |

Plus **Apply Filter** / **Reset** buttons, a **Refresh** button, and `Page n of m` pagination
(15 per page).

### 3.2 The session table (columns, in order)

| Column | Meaning | Why it's shown |
| :-- | :-- | :-- |
| **Session ID** | First 10 chars, links to detail | The identifier |
| **Source IP** | Originating attacker IP | Who |
| **Dominant Intent** | The session's main goal (colour badge) | The headline classification |
| **Attack Stage** | Furthest lifecycle stage reached | How far they got |
| **Risk** | Risk score 0–100 with a coloured bar | Danger at a glance |
| **Severity** | LOW/MEDIUM/HIGH/CRITICAL badge | Triage tier |
| **Events / Cmds** | `total_events / command_count` | Activity volume |
| **Last Seen** | Most recent activity time | Recency |
| **Action** | **Inspect** link → session detail | Drill-down |

Empty state: *"No Sessions Found — No attacker sessions matching the query criteria."*

---

## 4. Page — Session Detail (`/sessions/:id`)

The deepest view: the full **story of one attack**. This is the page that best demonstrates
the project's thesis (intent + stage + risk + explainability, per command). It loads three
things in parallel: the session, its events (`limit=150`), and its MITRE techniques.

**Top bar:** a **Back to Sessions** link, and a **Session State** badge — `ACTIVE` (emerald)
or `CLOSED` (slate).

### 4.1 Hero header card
- **Title** `Session: {id}`; sub-line shows **Source IP** (links to the attacker profile),
  optional **User**, and **Protocol** (default SSH).
- **Right stat box:** **Deterministic Threat Risk** (the 0–100 score, large) and **Threat
  Tier** (severity badge). *"Deterministic"* is deliberate wording — the risk score comes from
  a transparent, rule-based engine, not a model guess, so it is reproducible and explainable.
- **Quick metrics (4):** **Duration** (seconds), **Total Events**, **Commands Executed**
  (`count (unique)`), **Login Attempts**. *Why:* the behavioural fingerprint of the session —
  these same counts feed the risk engine's behavioural boosters.

### 4.2 Google Gemini AI Session Analyst (purple banner)
- Labelled with an **"ASSISTANT"** pill — signalling it's an *optional aid*, not the system's
  decision engine.
- Button **Analyze Session with AI** → `POST /api/sessions/{id}/analyze`. Produces an
  **Adversary Assessment Report** with: **Deduced Objective**, **Threat Actor
  Interpretation**, **Recommended Defensive Response**, and a numbered **Attack Progression
  Breakdown**. The engine used is shown as a pill (`Engine: …`).
- *Why it's here and clearly separated:* it turns the structured data into a readable
  narrative for a report, but the badge/labelling makes clear the core classification already
  happened without it.

### 4.3 MITRE + trajectory (two cards)
- **Detected MITRE ATT&CK Techniques** — one badge per mapped technique (technique ID + name,
  linking to the official MITRE page). *Why:* grounds every intent in the industry-standard
  ATT&CK framework — credibility and shared vocabulary.
- **Multi-Stage Attack Trajectory** — the **Intent Flow** (chevron-separated sequence of
  intents in order) and the **Furthest MITRE Stage Reached**. *Why:* this is the
  "reconnaissance → discovery → credential-access → …" progression that is the project's
  headline capability.

### 4.4 Chronological Attack Timeline & Telemetry Log
The full ordered list of events. Each row shows: index `#`, the **command** (as code) or event
type, its **intent badge**, **severity badge**, **stage**, **risk**, local time, and the
**explanation** — either a purple **Gemini AI Analysis** block (`ai_reason`) or a **Rule
Match** line (`rule_evidence`). *Why:* every single decision carries its evidence inline —
this is the "explainable" promise made concrete.

---

## 5. Page — Attacker Profiles (`/attackers`)

Heading **"Attacker Host Intelligence Profiles"**, sub *"Total Unique Attacker IPs: {N}"*.
Aggregates *across sessions* by source IP. *Why:* an attacker who returns in five sessions is
one threat actor — this page treats them as one.

### 5.1 Attacker table (columns, in order)

| Column | Meaning |
| :-- | :-- |
| **Attacker IP** | The host (links to detail) |
| **Total Sessions** | How many connections from this IP |
| **Total Events** | Total actions across all its sessions |
| **Peak Risk** | Highest single-session risk (`maximum_risk`) |
| **Avg Risk** | Mean risk across its sessions |
| **Dominant Intent** | Its most common goal |
| **Stage** | Furthest stage this host reached |
| **Severity** | Its worst severity tier |
| **Last Seen** | Recency |
| **Action** | **Profile** link → detail |

Controls: **Refresh**, an IP **Search** box, and pagination. Empty state: *"No Attacker
Profiles — No distinct attacker hosts identified."*

---

## 6. Page — Attacker Detail (`/attackers/:ip`)

The per-host dossier. Loads the profile plus that host's sessions (`limit=50`) in parallel.

- **Hero card:** `Attacker IP: {ip}`, **First Seen** / **Last Seen**, and a right stat box with
  **Peak Risk Score** and **Threat Tier**.
- **Aggregated stats (4):** **Total Honeypot Sessions**, **Total Ingested Events**, **Average
  Risk Score**, **Dominant Intent**.
- **Associated Sessions:** heading *"Sessions Originating from {ip}"* then the same session
  table from §3.2 — so you can drill from a host straight into any of its sessions.

*Why:* answers "is this IP a persistent, escalating threat or a one-off scan?" — exactly the
profiling question the project targets.

---

## 7. Page — Threat Alerts (`/alerts`)

Heading **"Security & Threat Alerts"**, sub *"Trigger condition: Threat Risk Score ≥ 75 •
Total Alerts: {N}"*. *Why a separate page:* CRITICAL sessions are the ones that demand action;
they get their own high-visibility, rose-coloured queue.

- **Filters:** **Status** (All / OPEN / INVESTIGATING / RESOLVED) and **Severity** (All / HIGH
  / CRITICAL).
- **Alert cards** (not a table — stacked, red-bordered cards for urgency): each shows the alert
  ID, **severity** + **intent** badges, a **status** pill, the human-readable **reason**, then
  a meta line — **IP**, **Session** (first 10 chars), **Trigger Risk** (`/100`), **Stage**,
  **Time** — and an **Inspect Threat Session** button linking straight to §4.
- Empty state (the *good* state): *"Zero Critical Alerts — No threat sessions have exceeded the
  critical risk threshold (75/100)."*

---

## 8. Page — Analytics (`/analytics`)

Heading **"Threat Intelligence Analytics & Security Insights"**, sub *"Cross-dimensional
analysis across Honeypot Telemetry, Behavioral Intent, MITRE Attack Stages, and Risk Scores"*.
Fetches **six** analytics endpoints in parallel. *Why:* the Overview is "now"; Analytics is the
"zoom out and see patterns" page for the report's results section.

Panels, in order:

1. **Attack Telemetry Frequency & Active Sessions Over Time** — time-series area chart
   (`/analytics/timeline`).
2. **Intent × Threat Risk Matrix Heatmap** — a table of intent rows with inline risk meters
   (`/analytics/heatmap`): per intent, the **event count**, **average risk** (bar + `/100`),
   **peak risk**, and a low/med/high/crit distribution. *Why:* shows *which intents are most
   dangerous*, not just most common.
3. **MITRE Attack Stage Distribution** — horizontal bars of how many sessions reached each
   lifecycle stage (`/analytics/stages`).
4. **Threat Risk Score Distribution** — bar chart across the 4 risk tiers
   (`/analytics/risk-distribution`).
5. **Classified Attacker Intent Distribution** — the intent donut **plus a breakdown table**
   (Intent Category · Event Count · Share %).
6. **Session Risk Severity Tiers** — the severity bar chart **plus a breakdown table**
   (Severity Tier · Session Count · Share %).

---

## 9. Charts reference (type · what it plots · source)

| Chart | Type | Plots | Feed |
| :-- | :-- | :-- | :-- |
| **AttackTimeline** | Area (2 series) | Events (cyan) + Sessions (indigo) over time | `/analytics/timeline` |
| **IntentDistributionChart** | Donut + 2-column legend | Slice = event count per intent; tooltip shows count + % | `/analytics/intents` |
| **SeverityChart** | Vertical bars | Session count per severity tier | `/analytics/severity` |
| **StageDistributionChart** | Horizontal bars | Sessions per MITRE stage | `/analytics/stages` |
| **RiskDistributionChart** | Vertical bars (4 buckets) | Session count per risk band | `/analytics/risk-distribution` |
| **RiskHeatmap** | Table + inline meters | Avg/peak risk + tier split per intent | `/analytics/heatmap` |

> The heatmap is intentionally a **table with meters**, not a coloured grid — it packs four
> numbers per intent (count, average, peak, distribution) into one readable row, which a pure
> colour grid can't convey.

---

## 10. Colour & badge legends (why the colours mean what they mean)

Colour is information here, not decoration — the same intent is always the same colour across
every chart and badge, so you learn the palette once.

### 10.1 Intent colours (all 10)

| Intent | Colour | Hex |
| :-- | :-- | :-- |
| RECONNAISSANCE | cyan | `#06b6d4` |
| DISCOVERY | blue | `#3b82f6` |
| CREDENTIAL_ACCESS | amber | `#f59e0b` |
| EXECUTION | red | `#ef4444` |
| PRIVILEGE_ESCALATION | purple | `#a855f7` |
| PERSISTENCE | indigo | `#6366f1` |
| EXPLOITATION | rose | `#f43f5e` |
| EXFILTRATION | fuchsia | `#d946ef` |
| CLEANUP | teal | `#14b8a6` |
| OTHER | slate | `#64748b` |

Unknown values fall back to OTHER (slate) — the UI never crashes on an unexpected label.

### 10.2 Severity tiers

| Tier | Risk range | Colour | Note |
| :-- | :-- | :-- | :-- |
| LOW | 0–24 | emerald `#10b981` | calm |
| MEDIUM | 25–49 | amber `#f59e0b` | watch |
| HIGH | 50–74 | orange `#f97316` | serious |
| CRITICAL | 75–100 | rose `#f43f5e` | **dot pulses** — raises an alert |

### 10.3 Risk indicator (the 0–100 bar)

The `{score}/100` indicator recolours by band using the same thresholds: `≥75` rose ·
`50–74` orange · `25–49` amber · `<25` emerald. Consistent breakpoints mean a colour always
implies the same danger, wherever it appears.

### 10.4 Classification source badges (on every live event)

This is the **transparency layer** — every event tells you which engine classified it. For
`ML`/`HYBRID` it also appends the calibrated confidence (e.g. `ML 92%`).

| Source | Colour | Means |
| :-- | :-- | :-- |
| **HYBRID** | cyan | Rule + ML agreed (shows confidence) |
| **ML** | violet | ML classifier decided (shows confidence) |
| **RULE** | slate | A deterministic rule matched |
| **GEMINI** | amber | The optional LLM decided a novel/ambiguous case |
| **FALLBACK** | rose | Degraded path (no engine was confident) |

> **Why surface the source at all?** Because the project's claim is *explainable* profiling.
> Seeing `HYBRID 92%` vs `RULE` vs `GEMINI` on each row proves the hybrid engine is real and
> lets an analyst trust (or question) any single decision.

---

## 11. Live-update mechanics (how "real time" works)

- A reusable `useWebSocket` hook connects over `ws://`/`wss://` (auto-matching the page
  protocol), reports status `CONNECTING → LIVE → DISCONNECTED`, sends a keepalive ping every
  15 s, and **auto-reconnects ~3 s** after any drop. *Why:* a dropped socket silently
  reconnects, so the live view is resilient during a long demo.
- **`/ws/events`** (Overview): new events are de-duplicated by `event_id`, prepended to the
  live list (kept to 8), bump **Total Events**, and update the intent donut in place.
- **`/ws/alerts`** (Overview): new alerts are de-duplicated by `alert_id`, prepended (kept to
  5), and bump **Critical Alerts**.
- Every other page loads on open and via its **Refresh** button / filter changes. *Why the
  split:* live streaming is valuable on the "now" screen; the analytical pages are snapshots
  you deliberately refresh.

---

## 12. Complete API surface behind the dashboard

Every screen element above is backed by one of these endpoints (Axios client, base `/api`,
30 s timeout). Useful for the report's "system interface" section.

| Endpoint | Feeds |
| :-- | :-- |
| `GET /api/health` | Navbar status badges |
| `GET /api/dashboard/stats` | Overview KPI cards |
| `GET /api/events` / `…/recent` | Session detail log / live feed |
| `GET /api/sessions` / `…/{id}` | Sessions list / detail |
| `POST /api/sessions/{id}/analyze` | Gemini analyst report |
| `GET /api/sessions/{id}/mitre` | MITRE techniques card |
| `GET /api/attackers` / `…/{ip}` | Attacker list / detail |
| `GET /api/alerts` | Alerts page + Overview alerts panel |
| `GET /api/analytics/intents` | Intent donut + table |
| `GET /api/analytics/severity` | Severity bars + table |
| `GET /api/analytics/timeline` | Timeline area chart |
| `GET /api/analytics/stages` | Stage distribution bars |
| `GET /api/analytics/risk-distribution` | Risk band bars |
| `GET /api/analytics/heatmap` | Intent × risk heatmap |
| `WS /ws/events`, `WS /ws/alerts` | Live Overview updates |

---

## 13. One-paragraph summary (paste-ready)

> The analyst dashboard is a dark-themed React 19 single-page application with five sections —
> Overview, Live Sessions, Attacker Profiles, Threat Alerts, and Analytics — served by a
> FastAPI backend over REST, with two WebSocket channels driving live updates on the Overview
> page. It visualises the full profiling pipeline: per-command **intent** (10 MITRE-aligned
> classes, each with a fixed colour), **attack stage** (kill-chain position), an explainable
> **risk score** (0–100, four severity tiers, alerting at ≥75), and a **classification-source
> badge** on every event (`RULE`/`ML`/`HYBRID`/`GEMINI`/`FALLBACK`, with ML confidence) that
> makes each decision auditable. Session-detail and attacker-detail views assemble individual
> commands into a multi-stage attack **trajectory**, and an *optional* Gemini "Session Analyst"
> turns that trajectory into a written adversary assessment — clearly labelled as an assistant,
> reflecting the system's design principle that ML is mandatory and the LLM is optional.
