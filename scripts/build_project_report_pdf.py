r"""
Build the INT-AWARE Project Status, Enhancements & Novelty report as a PDF.

One-off report generator (reportlab Platypus). Every claim/metric here is taken
verbatim from committed artifacts: PROJECT_AUDIT.md, ROADMAP.md, README.md,
docs/evaluation/evaluation_report.md, metrics.json, and the git history of the
`remediation/int-aware` branch. No numbers are invented.

Run:
    .\.venv\Scripts\python.exe scripts/build_project_report_pdf.py
Output:
    INT-AWARE_Status_Enhancements_Novelty.pdf   (repo root)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether, HRFlowable,
)

# ------------------------------------------------------------------ palette ---
NAVY = colors.HexColor("#0F2A47")      # primary / section bands
STEEL = colors.HexColor("#1F4E79")     # sub-headings
TEAL = colors.HexColor("#0E8F9B")      # accent
AMBER = colors.HexColor("#B45309")     # pending / caution
GREEN = colors.HexColor("#15803D")     # done
RED = colors.HexColor("#B91C1C")       # critical
INK = colors.HexColor("#1F2937")       # body text
MUTE = colors.HexColor("#6B7280")      # muted text
LIGHT = colors.HexColor("#EEF2F7")     # alt row
CARD = colors.HexColor("#F5F8FC")      # callout background
LINE = colors.HexColor("#CBD5E1")      # grid

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

# ------------------------------------------------------------------ styles ----
ss = getSampleStyleSheet()

body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica",
                      fontSize=9.6, leading=14, textColor=INK, alignment=TA_JUSTIFY,
                      spaceAfter=6)
body_l = ParagraphStyle("body_l", parent=body, alignment=TA_LEFT)
small = ParagraphStyle("small", parent=body, fontSize=8.4, leading=11.5, textColor=MUTE)
cell = ParagraphStyle("cell", parent=body, fontSize=8.6, leading=11.5, alignment=TA_LEFT, spaceAfter=0)
cell_b = ParagraphStyle("cell_b", parent=cell, fontName="Helvetica-Bold")
cellh = ParagraphStyle("cellh", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)
h2 = ParagraphStyle("h2", parent=ss["Normal"], fontName="Helvetica-Bold",
                    fontSize=12, leading=15, textColor=STEEL, spaceBefore=12, spaceAfter=5)
h3 = ParagraphStyle("h3", parent=ss["Normal"], fontName="Helvetica-Bold",
                    fontSize=10.3, leading=13, textColor=NAVY, spaceBefore=8, spaceAfter=3)
band_style = ParagraphStyle("band", parent=ss["Normal"], fontName="Helvetica-Bold",
                            fontSize=13, leading=16, textColor=colors.white)
kicker = ParagraphStyle("kicker", parent=ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=8.5, leading=11, textColor=TEAL)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, style=body):
    return Paragraph(t, style)


def band(text):
    """Full-width coloured section band."""
    t = Table([[Paragraph(esc(text), band_style)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether([Spacer(1, 6), t, Spacer(1, 8)])


def bullets(items, style=body_l, bullet_color=TEAL, gap=3):
    lis = []
    for it in items:
        para = it if isinstance(it, Paragraph) else Paragraph(it, style)
        lis.append(ListItem(para, spaceBefore=gap))
    return ListFlowable(
        lis, bulletType="bullet", bulletChar="•",
        bulletColor=bullet_color, bulletFontSize=8, leftIndent=14, bulletOffsetY=1,
    )


def mktable(rows, col_w, header=True, align=None, font=8.6, header_bg=NAVY):
    """rows: list of list of str/Paragraph. First row is header when header=True."""
    data = []
    for r_i, row in enumerate(rows):
        out = []
        for c_i, c in enumerate(row):
            if isinstance(c, Paragraph):
                out.append(c)
            else:
                st = cellh if (header and r_i == 0) else cell
                out.append(Paragraph(esc(str(c)), st))
        data.append(out)
    t = Table(data, colWidths=col_w, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("LINEAFTER", (0, 0), (-2, -1), 0.4, LINE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ]
        for r in range(1, len(data)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    if align:
        for (c0, c1, a) in align:
            style.append(("ALIGN", (c0, 0), (c1, -1), a))
    t.setStyle(TableStyle(style))
    return t


def callout(title, para, bg=CARD, bar=TEAL):
    inner = [Paragraph(esc(title), ParagraphStyle("cot", parent=h3, textColor=bar, spaceBefore=0))]
    if isinstance(para, list):
        inner += para
    else:
        inner.append(Paragraph(para, body_l))
    box = Table([[inner]], colWidths=[CONTENT_W])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
    ]))
    return KeepTogether([Spacer(1, 4), box, Spacer(1, 6)])


def tag(text, color):
    return f'<font color="{color.hexval()[2:] and ("#" + color.hexval()[2:])}"><b>{esc(text)}</b></font>'


def status(text, color):
    return Paragraph(f'<b><font color="#{color.hexval()[2:]}">{esc(text)}</font></b>', cell)


# ------------------------------------------------------------------ header/footer
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.2 * cm, PAGE_W - MARGIN, 1.2 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTE)
    canvas.drawString(MARGIN, 0.85 * cm, "INT-AWARE  —  Project Status, Enhancements & Novelty")
    canvas.drawRightString(PAGE_W - MARGIN, 0.85 * cm, "Page %d" % doc.page)
    canvas.restoreState()


# ================================================================== story =====
story = []

# ---- Title page ----
story.append(Spacer(1, 1.4 * cm))
tband = Table([[Paragraph(
    '<font color="white"><b>INT-AWARE</b></font>', ParagraphStyle(
        "tt", fontName="Helvetica-Bold", fontSize=30, leading=34, textColor=colors.white))]],
    colWidths=[CONTENT_W])
tband.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 18),
    ("TOPPADDING", (0, 0), (-1, -1), 18),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
sband = Table([[Paragraph(
    '<font color="#CFE8EC">Intent-Aware Deception System for Real-Time Attacker Profiling</font>',
    ParagraphStyle("st", fontName="Helvetica", fontSize=13, leading=17, textColor=colors.white))]],
    colWidths=[CONTENT_W])
sband.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 18),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
]))
story += [tband, sband, Spacer(1, 4)]
story.append(Table([[Paragraph(
    '<font color="white"><b>Project Status &nbsp;|&nbsp; Enhancement Backlog &nbsp;|&nbsp; Novelty Analysis</b></font>',
    ParagraphStyle("bx", fontName="Helvetica-Bold", fontSize=11, textColor=colors.white))]],
    colWidths=[CONTENT_W], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)])))
story.append(Spacer(1, 1.0 * cm))

meta = mktable([
    ["Field", "Value"],
    ["Report date", "11 September 2026"],
    ["Author", "Rakshita Shetty"],
    ["Repository branch", "remediation/int-aware  (base: master)"],
    ["Source of truth", "PROJECT_AUDIT.md, ROADMAP.md, README.md, docs/evaluation/*, git log"],
    ["Stack", "Cowrie honeypot -> FastAPI + calibrated ML + optional Gemini -> MongoDB -> React"],
    ["Test suite", "82 test functions across 18 modules (hermetic; 74 at audit baseline)"],
    ["Honest ML accuracy", "94.49% same-template held-out  /  67.87% leave-families-out (generalisation)"],
], [4.2 * cm, CONTENT_W - 4.2 * cm])
story.append(meta)
story.append(Spacer(1, 0.7 * cm))
story.append(callout(
    "About this document",
    "This report summarises (1) what has actually been built and verified in INT-AWARE, "
    "(2) the enhancement backlog you can pull from next, and (3) a candid analysis of where the "
    "genuine, defensible novelty of the project lies. In keeping with the project's own "
    "anti-fabrication rule, every figure is quoted from committed artifacts and each proposed "
    "feature is clearly labelled as <b>done</b>, <b>in progress</b>, or <b>proposed</b>."))
story.append(PageBreak())

# ============================================================ 1. EXEC SUMMARY =
story.append(band("1.  Executive Summary"))
story.append(P(
    "INT-AWARE is a full-stack cyber-deception platform. A real Cowrie SSH/Telnet honeypot "
    "(emulated shell — nothing ever executes on the host) writes JSON event logs; a FastAPI "
    "backend tails those logs in real time, classifies each command's <b>attacker intent</b> "
    "across a 10-class MITRE-aligned taxonomy, scores risk on a deterministic 0–100 scale, "
    "aggregates per-session and per-attacker intelligence into MongoDB, and streams everything to "
    "a React analyst dashboard over REST and WebSockets."))
story.append(P(
    "The engineering core is real and, in several places, genuinely well-built: the honeypot is "
    "safely isolated, the log tailer is rotation- and truncation-aware, the classifier arbitration "
    "is coherent, the risk engine is additive and explainable, MongoDB is indexed, and the test "
    "suite is hermetic and green. A formal read-only technical audit (2026-09-10) confirmed the "
    "system is <b>not fabricated</b> — the frontend shows no invented data — while identifying "
    "15 findings across correctness, integrity, and capability. A remediation roadmap of 13 phases "
    "now closes those findings one commit at a time; the highest-severity correctness bug (a "
    "structurally unreachable alert subsystem) has already been fixed and verified."))
story.append(callout(
    "The one-line takeaway",
    "You have a working, honestly-evaluated deception pipeline with a solid deterministic core. "
    "The remaining value — and the <b>novelty</b> — lies in the “intelligence” layer: teaching the "
    "system to say <i>“I don't know / this is novel”</i>, to <i>predict the next move</i>, and to keep the "
    "LLM strictly advisory. Those three capabilities are what turn a good classifier into a "
    "publishable contribution.", bar=TEAL))

# ============================================================ 2. WHAT IS BUILT =
story.append(band("2.  What Has Been Built (current, verified state)"))

story.append(P("2.1  End-to-end pipeline", h2))
story.append(P(
    "The verified data path (confirmed across <b>docker-compose.yml</b>, <b>log_collector.py</b>, "
    "<b>pipeline.py</b>, and <b>persistence_service.py</b>) is:", body))
story.append(mktable([
    ["Stage", "Component", "What it does"],
    ["1  Capture", "Cowrie honeypot", "Emulated SSH shell on loopback 127.0.0.1:2222; writes cowrie.json"],
    ["2  Ingest", "AsyncLogCollector", "Binary, rotation- and truncation-safe tail of the JSON log"],
    ["3  Normalise", "EventNormalizer", "JSON line -> NormalizedEvent with deterministic sha256 id"],
    ["4  Features", "FeatureExtractor / SessionAggregator", "Incremental per-session behavioural features (tokenise only)"],
    ["5  Classify", "HybridClassifier", "Rule -> calibrated ML -> optional Gemini, with recorded source"],
    ["6  Score", "RiskEngine", "Additive, explainable 0–100 event risk; deterministic"],
    ["7  Profile", "SessionIntelligence", "Cumulative session risk, stage reach, attacker aggregation"],
    ["8  Persist", "PersistenceService", "MongoDB: events / sessions / attackers / alerts (indexed)"],
    ["9  Serve", "FastAPI + WebSockets", "20 REST endpoints + live /ws/events and /ws/alerts"],
    ["10  Present", "React dashboard", "7 analyst pages: dashboard, sessions, attackers, alerts, analytics"],
], [2.6 * cm, 4.6 * cm, CONTENT_W - 7.2 * cm]))

story.append(P("2.2  Core capabilities (present today)", h2))
story.append(bullets([
    "<b>Hybrid intent classification</b> — a three-source engine with an auditable precedence: a "
    "deterministic rule matcher, a calibrated LinearSVC ML core (TF-IDF word + char n-grams), and "
    "an <i>optional</i> Google Gemini 2.5 Flash layer for novel/ambiguous commands. Every event records "
    "which source decided it (RULE / ML / HYBRID / GEMINI / FALLBACK).",
    "<b>Deterministic risk scoring</b> — an additive 0–100 engine with severity mapping; the LLM can "
    "never move a score (“AI boundary enforcement”).",
    "<b>MITRE ATT&amp;CK mapping</b> — per-session tactic / technique attribution with evidence.",
    "<b>Attacker profiling</b> — persistent per-IP profiles with multi-session behavioural history.",
    "<b>Live streaming</b> — real-time event and (now working) alert broadcast over WebSockets.",
    "<b>Analytics</b> — intent distribution, severity breakdown, timelines, risk histograms, source heatmaps.",
    "<b>Privacy by design</b> — passwords redacted to [REDACTED] before persistence; credentials never broadcast.",
]))

story.append(P("2.3  Intent taxonomy (10 MITRE-aligned classes)", h2))
story.append(mktable([
    ["Intent", "MITRE tactic", "Example"],
    ["RECONNAISSANCE", "TA0043", "uname -a, whoami"],
    ["DISCOVERY", "TA0007", "ps aux, netstat -antp"],
    ["CREDENTIAL_ACCESS", "TA0006", "cat /etc/shadow"],
    ["EXECUTION", "TA0002", "wget .../payload.sh"],
    ["PRIVILEGE_ESCALATION", "TA0004", "sudo su -"],
    ["PERSISTENCE", "TA0003", "echo ... >> authorized_keys"],
    ["EXPLOITATION", "TA0002", "() { :;}; echo VULN"],
    ["EXFILTRATION", "TA0010", "tar czf loot.tar.gz /etc"],
    ["CLEANUP", "TA0005", "rm -rf /var/log/auth.log"],
    ["OTHER", "—", "login telemetry, benign input"],
], [4.8 * cm, 3.0 * cm, CONTENT_W - 7.8 * cm]))

story.append(P("2.4  Honest ML performance (both splits, as committed in metrics.json)", h2))
story.append(mktable([
    ["Evaluation split", "Accuracy", "Macro F1", "Test N"],
    ["Primary (same-template 80/20, de-duplicated)", "94.49%", "0.9229", "272"],
    ["Robustness (leave-families-out = true generalisation)", "67.87%", "0.5267", "305"],
    ["5-fold CV (LinearSVC)", "85.39% ± 1.8%", "—", "—"],
], [CONTENT_W - 9.6 * cm, 3.4 * cm, 3.2 * cm, 3.0 * cm],
    align=[(1, 3, "CENTER")]))
story.append(P(
    "Dataset: 1,360 unique commands across 242 template families, class-imbalanced "
    "(EXECUTION 318 ... PRIV_ESC 57). Weakest class RECONNAISSANCE (F1 0.714). The ~27-point gap "
    "between the two splits is reported openly, not hidden — it is precisely the room the hybrid "
    "rule + LLM layers exist to cover at runtime.", small))

story.append(P("2.5  Quality gates", h2))
story.append(bullets([
    "<b>82 test functions</b> across 18 modules, fully hermetic (mongomock, mocked Gemini, tempfiles) — "
    "no live database or network needed. Strong exact-value assertions, not filler.",
    "<b>CI</b> (GitHub Actions): pytest on Python 3.13 plus an advisory pip-audit dependency scan.",
    "<b>Host safety verified</b>: no path exists by which attacker input executes on the host — "
    "emulated shell, loopback-only, read-only log mount, no exec/subprocess in the ingest path.",
]))

# ============================================================ 3. PROGRESS ======
story.append(PageBreak())
story.append(band("3.  Remediation Progress (audit -> roadmap -> done)"))
story.append(P(
    "A read-only audit produced 15 prioritised findings (F1–F15). The companion roadmap turns them "
    "into 13 phases. The table below is the live status; “done” items are backed by commits on the "
    "<b>remediation/int-aware</b> branch.", body))

story.append(mktable([
    ["ID", "Pri", "Finding", "Status"],
    ["F4", "P0", "No git history; repo rooted at $HOME", status("DONE", GREEN)],
    ["—", "P0", "CI: hermetic pytest + advisory pip-audit (Phase 0)", status("DONE", GREEN)],
    ["F1", "P0", "Alert subsystem unreachable (event risk cap 65 vs 75 gate)", status("DONE", GREEN)],
    ["F5", "P1", "Gemini request timeout configured but never enforced", status("DONE", GREEN)],
    ["F6", "P1", "Unbounded in-memory growth of session / dedup caches", status("DONE", GREEN)],
    ["F7", "P1", "update_attacker recompute was O(sessions) per event", status("DONE", GREEN)],
    ["F2", "P0", "Optimistic accuracy framing (foreground honest split)", status("PENDING", AMBER)],
    ["F3", "P0", "Eval CSVs contradict prose; no latency percentiles", status("PENDING", AMBER)],
    ["F8", "P1", "No novelty/OOD/abstention; no predictive next-intent", status("PROPOSED", RED)],
    ["F9", "P1", "No auth/TLS; nginx headers; CORS too broad", status("PENDING", AMBER)],
    ["F10", "P2", "ML stack untested; adversarial/load offline-only", status("PENDING", AMBER)],
    ["F11", "P2", "Root containers; mutable tags (CVE scan added, advisory)", status("PARTIAL", AMBER)],
    ["F12", "P2", "Weak Gemini payload sanitisation; analyst lacks schema", status("PENDING", AMBER)],
    ["F13", "P3", "Misleading frontend fallbacks (null IP -> 127.0.0.1)", status("PENDING", AMBER)],
    ["F14", "P3", "Doc drift (Motor vs pymongo; Python 3.12 vs 3.13)", status("PENDING", AMBER)],
    ["F15", "P3", "GET /api/events/recent untested", status("PENDING", AMBER)],
], [1.2 * cm, 1.1 * cm, CONTENT_W - 5.1 * cm, 2.8 * cm],
    align=[(1, 1, "CENTER"), (3, 3, "CENTER")]))

story.append(P("Committed on the remediation branch", h3))
story.append(mktable([
    ["Commit", "What it delivered"],
    ["472b99e", "Baseline snapshot; repo re-rooted in the project (closes F4)"],
    ["21d6ce2", "CI workflow: hermetic pytest + advisory pip-audit (Phase 0)"],
    ["382a724", "Alerts now driven by session cumulative risk, not event risk (F1)"],
    ["b37db46", "Enforce configured Gemini request timeout (F5)"],
    ["ed03575", "Bound session + dedup caches to prevent unbounded growth (F6)"],
    ["9d7e2f4", "Attacker profile via server-side aggregation, O(1)-ish per event (F7)"],
], [2.6 * cm, CONTENT_W - 2.6 * cm]))
story.append(P(
    "Net effect: all P0 correctness (F1, F4) and all P1 reliability findings (F5–F7) are closed. "
    "What remains is scientific-integrity polish (F2, F3), security hardening (F9), test depth "
    "(F10), and — most importantly for novelty — the intelligence capabilities in F8.", body))

# ============================================================ 4. BACKLOG =======
story.append(PageBreak())
story.append(band("4.  Features You Can Add"))
story.append(P(
    "Two tiers. Tier A is the enhancement backlog already scoped in your roadmap (Phases 4–12) — "
    "each ships with a measurable success criterion. Tier B is a set of higher-ambition ideas that "
    "go beyond the current roadmap and would most sharply raise the project's originality.", body))

story.append(P("Tier A — On your existing roadmap (scoped, sequenced)", h2))
story.append(mktable([
    ["Phase", "Feature", "Why it matters"],
    ["P4", "Novelty / OOD / abstention", "System can output KNOWN / AMBIGUOUS / LOW-CONF / NOVEL instead of forcing 1-of-10"],
    ["P5", "Predictive next-intent + sequence model", "Forecast the next tactic; label OBSERVED / INFERRED / PREDICTED"],
    ["P6", "Decomposable risk v2 + alert priority", "Itemised, summable risk contributions; ordered alert feed"],
    ["P7", "Behavioural attacker profiling + MITRE depth", "Cluster attacker archetypes; tactic->technique->sub-technique"],
    ["P8", "Security hardening", "API auth, WS origin/cap, tight CORS, nginx headers, non-root containers"],
    ["P9", "Adversarial-robustness CI gate", "Promote unseen A/B/C/D set into a regression-gated metric"],
    ["P10", "ML-stack + regression tests", "Load the real .joblib; fail CI if held-out accuracy drops"],
    ["P11", "Observability + honest benchmarks", "Structured logs, per-stage latency p50/p95/p99 on documented HW"],
    ["P12", "Analyst dashboard + doc rewrite", "Surface determinations, predictions, risk decomposition; fix fallbacks"],
], [1.3 * cm, 5.3 * cm, CONTENT_W - 6.6 * cm]))

story.append(P("Tier B — Beyond the roadmap (originality boosters)", h2))
story.append(P(
    "These are my additions — not in your current roadmap. Each is tagged by how much it raises "
    "novelty. All can be built without violating the host-safety or no-fabrication rules.", small))

def feat(title, novelty, ncolor, text):
    head = Paragraph(
        f'<font color="#{TEAL.hexval()[2:]}"><b>•</b></font>&nbsp; <b>{esc(title)}</b> '
        f'&nbsp;<font size="7.5" color="#{ncolor.hexval()[2:]}"><b>[{esc(novelty)}]</b></font>',
        ParagraphStyle("ft", parent=body_l, leftIndent=6, spaceBefore=5, spaceAfter=1))
    sub = Paragraph(text, ParagraphStyle("fs", parent=body_l, fontSize=9, leading=12.5,
                                         textColor=INK, leftIndent=16, spaceAfter=2))
    return KeepTogether([head, sub])

for kt in [
    feat("Adaptive / intent-driven deception", "HIGH novelty", RED,
        "Use the <i>predicted</i> next intent to change what the emulated shell reveals in real time — e.g. "
        "dangle a fake credential file when CREDENTIAL_ACCESS is forecast, or a fake DB dump when "
        "EXFILTRATION looks imminent. This closes the loop from passive profiling to active engagement."),
    feat("Behavioural attacker fingerprinting (cross-IP re-identification)", "HIGH novelty", RED,
        "Command-style “stylometry” — timing rhythm, typo/retry patterns, tool signatures, command "
        "ordering — to link sessions from different source IPs to a single actor. Turns per-IP profiles "
        "into per-<i>actor</i> profiles."),
    feat("Active-learning feedback loop", "MED-HIGH novelty", AMBER,
        "Let an analyst confirm or correct a determination in the dashboard; corrections feed a "
        "retraining queue and a drift monitor. Directly attacks the 67.87% generalisation gap over time."),
    feat("Campaign graph correlation", "MED-HIGH novelty", AMBER,
        "Build a graph over attackers / sessions / techniques / payload hashes to surface coordinated "
        "campaigns and shared infrastructure, not just isolated sessions."),
    feat("Calibration &amp; drift dashboard", "MED novelty", TEAL,
        "Reliability diagrams, Expected Calibration Error over time, per-class drift — a natural, "
        "on-brand extension of the project's scientific-integrity theme, and it feeds the abstention thresholds."),
    feat("LLM-authored SOC narrative (guarded)", "MED novelty", TEAL,
        "One-click natural-language session report + auto MITRE writeup, under the same non-authoritative, "
        "schema-validated, never-executed guardrails already used for classification."),
    feat("Threat-intel enrichment", "MED (integration)", TEAL,
        "Read-only, cached lookups (GreyNoise / AbuseIPDB / Tor-exit) to add reputation context to each "
        "source IP. Enriches profiles without touching the deterministic risk authority."),
    feat("Interop exports: STIX/TAXII, MISP, SIEM/SOAR webhooks", "MED (integration)", TEAL,
        "Emit findings to Slack / Splunk / Elastic and export indicators in standard formats — makes the "
        "platform deployable inside a real SOC."),
]:
    story.append(kt)

# ============================================================ 5. NOVELTY =======
story.append(PageBreak())
story.append(band("5.  Novelty — What Actually Makes This Publishable"))
story.append(P(
    "Honest starting point: honeypots (Cowrie), supervised command-intent classifiers, LLM security "
    "assistants, and MITRE mapping all already exist <i>individually</i>. So the novelty of INT-AWARE is "
    "<b>not</b> any one of those parts. It is (a) the <b>trust architecture</b> that binds them and "
    "(b) two capabilities that most deployed classifiers simply do not have. Below, each pillar is "
    "marked with whether it exists today or is on the roadmap — so the contribution can be stated "
    "without over-claiming.", body))

story.append(callout(
    "The contribution, in one sentence",
    "<i>An intent-aware honeypot-analytics pipeline in which a probabilistic ML core and an optional "
    "LLM operate strictly beneath a deterministic, explainable authority — extended so the system "
    "can flag NOVEL / unknown attacker behaviour (abstention) and forecast the next tactic with "
    "explicit epistemic provenance (OBSERVED / INFERRED / PREDICTED).</i>", bar=NAVY, bg=CARD))

story.append(P("Pillar 1 — A deterministic-authority trust boundary for LLMs in security", h2))
story.append(Paragraph('<b>Status: IMPLEMENTED today.</b>', kicker))
story.append(P(
    "The Gemini layer is consulted <i>only</i> for commands where both the rule engine is weak and the ML "
    "core is not confident. Its output is schema-constrained, temperature-pinned, validated, and "
    "<b>never executed</b>. Crucially, it can never change a risk score — all risk, severity, and "
    "alerting are computed by a deterministic additive engine, and the whole system runs fully with "
    "the LLM switched off (graceful degradation). Most LLM-in-security work either lets the model "
    "drive decisions (opaque, prompt-injectable, irreproducible) or bolts it on as an unchecked black "
    "box. Demonstrating a <b>reproducible, falsifiable</b> pipeline where the LLM is provably "
    "subordinate to a glass-box core is a genuine trustworthy-AI contribution, not just plumbing.", body))

story.append(P("Pillar 2 — Intent-awareness WITH abstention and novelty detection", h2))
story.append(Paragraph('<b>Status: ROADMAP (Phase 4). Designed, dataset ready, not yet built.</b>', kicker))
story.append(P(
    "Today the classifier always returns one of 10 classes — it cannot say “I don't know.” The "
    "proposed step: emit KNOWN / AMBIGUOUS / LOW-CONFIDENCE / NOVEL(OOD) using calibrated max-probability, "
    "top-2 margin, and an out-of-distribution score (distance to training centroids or a one-class "
    "model). Abstention and OOD detection on <i>honeypot command streams</i> is under-explored, and the "
    "unseen A/B/C/D evaluation set to validate it already exists in the repo. This is the single "
    "highest-leverage novelty item: “intent-<b>aware</b>” honestly requires the system to know the "
    "limits of what it knows.", body))

story.append(P("Pillar 3 — Predictive, provenance-labelled attack-stage intelligence", h2))
story.append(Paragraph('<b>Status: ROADMAP (Phase 5).</b>', kicker))
story.append(P(
    "Move from “what happened” to “what is likely next”: a transition model over observed intent "
    "sequences forecasts the next tactic with a calibrated probability. The distinctive twist is "
    "<b>epistemic provenance labelling</b> — every piece of intelligence is tagged OBSERVED (it "
    "happened), INFERRED (deduced from current state), or PREDICTED (a forecast) — so a prediction is "
    "never rendered as fact. That honesty-by-construction is itself a defensible design contribution "
    "and pairs naturally with adaptive deception (Tier B).", body))

story.append(P("Pillar 4 — Audit-driven, dual-split honest evaluation (methodological)", h2))
story.append(Paragraph('<b>Status: IMPLEMENTED / ongoing.</b>', kicker))
story.append(P(
    "Not research-novelty per se, but a real differentiator at this tier and a strengthener for any "
    "paper: both same-template (94.49%) and leave-families-out (67.87%) accuracy are reported, no "
    "metric is fabricated, every figure is regenerated from a seeded script, and a formal read-only "
    "audit drives a finding-by-finding remediation. Reviewers reward this; it is rare in "
    "student-tier security projects.", body))

story.append(P("How INT-AWARE sits against the alternatives", h2))
story.append(mktable([
    ["Approach", "Detects\nintent", "Says\nnovel/unknown", "Predicts\nnext step", "LLM used\nsafely", "Explainable\nrisk"],
    ["Raw Cowrie honeypot", "No", "—", "No", "—", "No"],
    ["Supervised command classifier", "Yes (forced)", "No", "No", "—", "No"],
    ["LLM-only SOC assistant", "Yes", "Sometimes", "Sometimes", "No (LLM decides)", "No (opaque)"],
    ["INT-AWARE — today", "Yes", "Not yet", "Not yet", "Yes", "Yes"],
    ["INT-AWARE — with P4–P6", "Yes", "Yes", "Yes", "Yes", "Yes (decomposable)"],
], [CONTENT_W - 5 * 2.5 * cm + 1.3 * cm] + [2.35 * cm] * 5,
    align=[(1, 5, "CENTER")], font=8.0))
story.append(P(
    "The last two rows are the pitch: the current system already occupies a defensible corner "
    "(safe LLM + explainable risk), and finishing Phases 4–6 lands the full “intent-aware, "
    "abstaining, predictive, explainable” claim — which no single row above matches.", small))

story.append(callout(
    "Candidate framings for a paper / viva",
    [bullets([
        "“Knowing what you don't know: abstention and novelty detection for honeypot command-intent classification.”",
        "“Advisory, not authoritative: a deterministic-core trust boundary for LLMs in cyber-deception.”",
        "“From detection to forecast: provenance-labelled next-intent prediction in an intent-aware honeypot.”",
    ], bullet_color=NAVY)],
    bar=TEAL))

# ============================================================ 6. NEXT STEPS ====
story.append(PageBreak())
story.append(band("6.  Recommended Next Steps (prioritised)"))
story.append(mktable([
    ["#", "Do this", "Because", "Effort"],
    ["1", "Phase 2: foreground the honest metric; reconcile eval CSVs vs prose",
     "Closes the last P0 integrity gap; protects credibility before adding features", "S"],
    ["2", "Phase 4: novelty / OOD / abstention",
     "The single biggest novelty lever; dataset already exists", "M"],
    ["3", "Phase 5: predictive next-intent with provenance labels",
     "Turns the classifier into forecasting; strong demo/viva moment", "M"],
    ["4", "Phase 10: load the real .joblib in tests + regression gate",
     "The ML stack is currently untested; protects the model claim", "S-M"],
    ["5", "Phase 8: baseline auth + nginx headers + non-root containers",
     "Required before any non-loopback demo; low-risk hardening", "M"],
    ["6", "Tier B: pick ONE originality booster (adaptive deception or fingerprinting)",
     "One well-executed Tier-B feature is what makes the project memorable", "M-L"],
], [0.8 * cm, 6.2 * cm, CONTENT_W - 9.0 * cm, 1.8 * cm],
    align=[(0, 0, "CENTER"), (3, 3, "CENTER")]))
story.append(Spacer(1, 6))
story.append(P("Effort key: S = small (hours), M = medium (days), L = larger (1–2 weeks).", small))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=0.6, color=LINE))
story.append(Spacer(1, 6))
story.append(P(
    "Every figure in this report is quoted from committed artifacts (PROJECT_AUDIT.md, ROADMAP.md, "
    "docs/evaluation/*, metrics.json) or the git history of remediation/int-aware, in keeping with "
    "the project's own no-fabrication rule. Items marked ROADMAP or PROPOSED are not yet implemented "
    "and are labelled as such throughout.", small))

# ------------------------------------------------------------------ build ------
if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "INT-AWARE_Status_Enhancements_Novelty.pdf")
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="INT-AWARE - Project Status, Enhancements & Novelty",
        author="Rakshita Shetty",
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("WROTE", out)
