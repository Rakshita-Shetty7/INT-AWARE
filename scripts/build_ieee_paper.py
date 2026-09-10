#!/usr/bin/env python3
"""
Build a genuine IEEE two-column conference paper (PDF) for the
Intent-Aware Deception System.

Pure-Python toolchain (no LaTeX, no system binaries):
    reportlab  -> two-column IEEE layout, tables, typography
    svglib     -> embed the real evaluation figures (SVG) as vector art
    numpy/PIL  -> (available; raster helpers)

All quantitative claims come from the project's real artefacts:
    backend/app/ml/artifacts/metrics.json  (94.49% acc, 0.9229 macro-F1, ...)
    docs/evaluation/*.svg                   (confusion matrix, per-class F1, ...)

Usage:
    .venv/Scripts/python.exe scripts/build_ieee_paper.py
Output:
    docs/pdf/INT-AWARE_IEEE_Paper.pdf
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    FrameBreak, NextPageTemplate, KeepTogether, Image as RLImage,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "pdf" / "INT-AWARE_IEEE_Paper.pdf"
EVAL = ROOT / "docs" / "evaluation"

# ---------------------------------------------------------------------------
# Page geometry — IEEE US-Letter two-column
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter            # 612 x 792 pt
LM = 0.625 * inch                  # 45 pt  left margin
RM = 0.625 * inch                  # 45 pt  right margin
TM = 0.72 * inch                   # top margin
BM = 0.78 * inch                   # bottom margin
GAP = 0.25 * inch                  # 18 pt  column gutter
COL_W = (PAGE_W - LM - RM - GAP) / 2.0     # 252 pt per column
BAND_H = 128                        # full-width title band on page 1
FIG_W = COL_W - 14                  # figure/table content width inside a column

NAVY = colors.HexColor("#0b3d91")
INK = colors.HexColor("#111111")
GRID = colors.HexColor("#333333")

# ---------------------------------------------------------------------------
# Glyph sanitisation (reportlab base-14 fonts use WinAnsi; map the rest)
# ---------------------------------------------------------------------------
_SAN = {
    "▸": ">", "▶": ">", "→": "->", "←": "<-",
    "≥": ">=", "≤": "<=", "α": "alpha", "×": "x",
    "∑": "sum", "≈": "~", "…": "...", "·": "-",
    "′": "'", "″": '"', "≡": "=",
    # box-drawing (unused now, but keep safe)
    "│": "|", "─": "-", "┌": "+", "┐": "+",
    "└": "+", "┘": "+", "▼": "v", "┴": "+", "┬": "+",
}


def san(t: str) -> str:
    for a, b in _SAN.items():
        t = t.replace(a, b)
    return t


_CODE = "\x00C%d\x00"


def md(text: str) -> str:
    """Inline markdown (**bold**, *italic*, `code`) -> reportlab mini-HTML."""
    text = san(text)
    codes: list[str] = []

    def grab(m):
        codes.append(m.group(1))
        return _CODE % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", grab, text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)

    def put(m):
        c = codes[int(m.group(1))]
        c = c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<font face="Courier" size="8">{c}</font>'

    text = re.sub(r"\x00C(\d+)\x00", put, text)

    # Re-enable the small whitelist of inline tags we author by hand. Everything
    # else stays escaped, so stray '<' in command text can never break the XML.
    for tag in ("b", "i", "sub", "super"):
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>").replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    text = text.replace("&lt;br/&gt;", "<br/>")
    return text


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
S = {
    "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=17.5,
                            leading=20, alignment=TA_CENTER, textColor=INK,
                            spaceBefore=2, spaceAfter=6),
    "author": ParagraphStyle("author", fontName="Times-Roman", fontSize=11.5,
                             leading=14, alignment=TA_CENTER, spaceAfter=1),
    "affil": ParagraphStyle("affil", fontName="Times-Italic", fontSize=9.5,
                            leading=12, alignment=TA_CENTER, spaceAfter=1),
    "abstract": ParagraphStyle("abstract", fontName="Times-Bold", fontSize=9,
                               leading=10.8, alignment=TA_JUSTIFY, spaceAfter=5),
    "keywords": ParagraphStyle("keywords", fontName="Times-Bold", fontSize=9,
                               leading=10.8, alignment=TA_JUSTIFY, spaceAfter=8),
    "body": ParagraphStyle("body", fontName="Times-Roman", fontSize=9.7,
                          leading=11.6, alignment=TA_JUSTIFY, firstLineIndent=10,
                          spaceAfter=1.5),
    "body0": ParagraphStyle("body0", fontName="Times-Roman", fontSize=9.7,
                           leading=11.6, alignment=TA_JUSTIFY, spaceAfter=1.5),
    "h1": ParagraphStyle("h1", fontName="Times-Bold", fontSize=10, leading=12,
                        alignment=TA_CENTER, spaceBefore=9, spaceAfter=3,
                        textColor=INK),
    "h2": ParagraphStyle("h2", fontName="Times-Italic", fontSize=9.8, leading=11.5,
                        alignment=TA_LEFT, spaceBefore=4, spaceAfter=1.5),
    "li": ParagraphStyle("li", fontName="Times-Roman", fontSize=9.7, leading=11.4,
                        alignment=TA_JUSTIFY, leftIndent=12, firstLineIndent=-9,
                        spaceAfter=1.5),
    "cap": ParagraphStyle("cap", fontName="Times-Roman", fontSize=8, leading=9.5,
                         alignment=TA_CENTER, spaceBefore=3, spaceAfter=7),
    "tnum": ParagraphStyle("tnum", fontName="Times-Roman", fontSize=8, leading=9.5,
                          alignment=TA_CENTER, spaceBefore=5, spaceAfter=0),
    "ttitle": ParagraphStyle("ttitle", fontName="Times-Roman", fontSize=8, leading=9.5,
                            alignment=TA_CENTER, spaceAfter=3),
    "ref": ParagraphStyle("ref", fontName="Times-Roman", fontSize=8.2, leading=9.8,
                         alignment=TA_LEFT, leftIndent=11, firstLineIndent=-11,
                         spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName="Times-Roman", fontSize=6.4, leading=7.6,
                          alignment=TA_LEFT),
    "cellh": ParagraphStyle("cellh", fontName="Times-Bold", fontSize=6.4, leading=7.6,
                           alignment=TA_LEFT, textColor=colors.white),
}

_FIG = [0]
_TAB = [0]
_ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


def fig_no() -> int:
    _FIG[0] += 1
    return _FIG[0]


def tab_no() -> str:
    _TAB[0] += 1
    return f"TABLE {_ROMAN[_TAB[0]]}"


def P(text, style="body"):
    return Paragraph(md(text), S[style])


def H1(roman, title):
    prefix = f"{roman}.&nbsp;&nbsp;" if roman else ""
    return Paragraph(f"{prefix}{san(title).upper()}", S["h1"])


def H2(letter_, title):
    return Paragraph(f"<i>{letter_}. {md(title)}</i>", S["h2"])


def OL(items):
    return [Paragraph(f"{i+1})&nbsp;&nbsp;{md(t)}", S["li"]) for i, t in enumerate(items)]


def UL(items):
    return [Paragraph(f"•&nbsp;&nbsp;{md(t)}", S["li"]) for t in items]


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------
def svg_fig(name, caption, width=FIG_W):
    d = svg2rlg(str(EVAL / name))
    sc = width / float(d.width)
    d.width, d.height = d.width * sc, d.height * sc
    d.scale(sc, sc)
    d.hAlign = "CENTER"
    cap = Paragraph(f"Fig. {fig_no()}.&nbsp;&nbsp;{md(caption)}", S["cap"])
    return KeepTogether([d, cap])


def arch_drawing(W):
    boxes = [
        ("Attacker   (SSH / Telnet, port 2222)", 0),
        ("Cowrie Honeypot   (ISOLATED shell emulation)", 0),
        ("Async Log Collector   (rotation-safe tail of cowrie.json)", 0),
        ("Feature Extraction   (per-session context)", 0),
        ("Hybrid Intent Classifier   [ Rule > ML > Gemini (opt.) ]", 1),
        ("Stage Mapper   |   Risk Engine (0-100)   |   Profiler", 0),
        ("MongoDB   (idempotent persistence)", 0),
        ("FastAPI   -   REST + WebSocket", 0),
        ("React Analyst Dashboard   (live, explainable)", 0),
    ]
    bh, gap = 21.0, 12.0
    n = len(boxes)
    H = n * bh + (n - 1) * gap
    d = Drawing(W, H)
    y = H - bh
    rows = []
    for label, hi in boxes:
        fill = colors.HexColor("#dbeafe") if hi else colors.HexColor("#f1f5f9")
        stroke = colors.HexColor("#1d4ed8") if hi else colors.HexColor("#94a3b8")
        d.add(Rect(2, y, W - 4, bh, rx=4, ry=4, fillColor=fill,
                   strokeColor=stroke, strokeWidth=1.2 if hi else 0.8))
        d.add(String(W / 2.0, y + bh / 2.0 - 2.4, label,
                     fontName="Times-Bold" if hi else "Times-Roman",
                     fontSize=6.8 if hi else 6.5, textAnchor="middle",
                     fillColor=colors.HexColor("#0f172a")))
        rows.append((y, y + bh))
        y -= (bh + gap)
    for i in range(n - 1):
        x = W / 2.0
        y_from = rows[i][0]
        y_to = rows[i + 1][1]
        d.add(Line(x, y_from, x, y_to + 4.5, strokeColor=colors.HexColor("#475569"),
                   strokeWidth=0.8))
        d.add(Polygon(points=[x - 2.8, y_to + 5.5, x + 2.8, y_to + 5.5, x, y_to + 1.0],
                      fillColor=colors.HexColor("#475569"),
                      strokeColor=colors.HexColor("#475569")))
    d.hAlign = "CENTER"
    cap = Paragraph(f"Fig. {fig_no()}.&nbsp;&nbsp;"
                    + md("End-to-end streaming architecture: honeypot capture "
                         "through hybrid classification, risk scoring, persistence, "
                         "and the live analyst dashboard."), S["cap"])
    return KeepTogether([d, cap])


# ---------------------------------------------------------------------------
# Table helper (booktabs / IEEE style)
# ---------------------------------------------------------------------------
def table(title, headers, rows, widths, aligns=None,
          fs=7.4, wrap=False, bold_last=False):
    """Renders an IEEE-style table with an auto-assigned TABLE <roman> number."""
    number = tab_no()
    tot = sum(widths)
    colw = [w / tot * FIG_W for w in widths]
    aligns = aligns or ["LEFT"] * len(headers)

    if wrap:
        head = [Paragraph(md(str(h)), S["cellh"]) for h in headers]
        data = [head] + [[Paragraph(md(str(c)), S["cell"]) for c in r] for r in rows]
    else:
        data = [list(headers)] + [list(r) for r in rows]

    t = Table(data, colWidths=colw, hAlign="CENTER", repeatRows=1)
    st = [
        ("FONT", (0, 0), (-1, 0), "Times-Bold", fs),
        ("FONT", (0, 1), (-1, -1), "Times-Roman", fs),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2fa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i, a in enumerate(aligns):
        st.append(("ALIGN", (i, 0), (i, -1), a))
    if bold_last:
        st.append(("FONT", (0, -1), (-1, -1), "Times-Bold", fs))
        st.append(("LINEABOVE", (0, -1), (-1, -1), 0.5, INK))
    t.setStyle(TableStyle(st))

    cap = [Paragraph(number, S["tnum"]),
           Paragraph(san(title).upper(), S["ttitle"])]
    return KeepTogether(cap + [t, Spacer(1, 6)])


# ---------------------------------------------------------------------------
# Page furniture
# ---------------------------------------------------------------------------
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(PAGE_W / 2.0, 30, str(canvas.getPageNumber()))
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(
        str(OUT), pagesize=letter,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
        title="Intent-Aware Deception: Real-Time Attacker Profiling",
        author="Rakshita Shetty",
    )

    band = Frame(LM, PAGE_H - TM - BAND_H, PAGE_W - LM - RM, BAND_H,
                 id="band", leftPadding=4, rightPadding=4, topPadding=2,
                 bottomPadding=2)
    fch = (PAGE_H - TM - BAND_H) - BM
    c1 = Frame(LM, BM, COL_W, fch, id="c1", leftPadding=6, rightPadding=6,
               topPadding=2, bottomPadding=2)
    c2 = Frame(LM + COL_W + GAP, BM, COL_W, fch, id="c2", leftPadding=6,
               rightPadding=6, topPadding=2, bottomPadding=2)
    full = PAGE_H - TM - BM
    lL = Frame(LM, BM, COL_W, full, id="lL", leftPadding=6, rightPadding=6,
               topPadding=2, bottomPadding=2)
    rL = Frame(LM + COL_W + GAP, BM, COL_W, full, id="rL", leftPadding=6,
               rightPadding=6, topPadding=2, bottomPadding=2)

    doc.addPageTemplates([
        PageTemplate(id="First", frames=[band, c1, c2], onPage=on_page),
        PageTemplate(id="Later", frames=[lL, rL], onPage=on_page),
    ])

    s = []  # story
    s.append(NextPageTemplate("Later"))

    # ---- Title band (full width) ----
    s.append(Paragraph(
        "Intent-Aware Deception: Real-Time Attacker Profiling via "
        "Hybrid Rule&ndash;ML Classification of Honeypot Command Streams",
        S["title"]))
    s.append(Paragraph("Rakshita Shetty", S["author"]))
    s.append(Paragraph("Department of Computer Science and Engineering", S["affil"]))
    s.append(Paragraph("<i>Intent-Aware Deception System &mdash; Research Project</i>",
                       S["affil"]))
    s.append(FrameBreak())

    # ---- Abstract + keywords (left column start) ----
    s.append(Paragraph(
        "<b><i>Abstract</i>&mdash;</b>" + md(
            "Traditional honeypots excel at capturing attacker activity but stop "
            "short of interpreting it: they log commands without inferring the "
            "adversary's underlying goal. We present an intent-aware deception "
            "system that transforms raw honeypot telemetry into real-time, "
            "explainable attacker profiles. Captured shell commands from an "
            "isolated medium-interaction honeypot are streamed through an "
            "asynchronous pipeline that normalises each command, extracts lexical "
            "features, and classifies it into one of ten MITRE ATT&CK-aligned intent "
            "classes using a hybrid classifier: a deterministic rule engine, a "
            "calibrated machine-learning core, and an optional large-language-model "
            "semantic layer, arbitrated by explicit confidence precedence. "
            "Per-session and per-attacker profiles are assembled into multi-stage "
            "attack trajectories, and each session receives an explainable risk "
            "score (0-100). The ML core - a calibrated linear support-vector machine "
            "over a combined word- and character-n-gram TF-IDF feature space - "
            "achieves 94.49% accuracy and 0.9229 macro-F1 on a leakage-controlled "
            "held-out set of 272 commands; a stricter leave-families-out protocol "
            "yields 67.87% accuracy, reported explicitly to characterise "
            "generalisation honestly. The full system runs end-to-end in real time "
            "and is reproducible from a fixed seed. Fusing deterministic rules, "
            "calibrated ML, and an optional LLM yields profiling that is "
            "simultaneously accurate, real-time, and auditable - a combination none "
            "of the three achieves alone."),
        S["abstract"]))
    s.append(Paragraph(
        "<b><i>Index Terms</i>&mdash;</b>" + md(
            "honeypot, cyber deception, attacker profiling, intent classification, "
            "MITRE ATT&CK, machine learning, text classification, threat "
            "intelligence, explainable security, support vector machine."),
        S["keywords"]))

    # ---- I. Introduction ----
    s.append(H1("I", "Introduction"))
    s.append(P("Honeypots - decoy systems with no legitimate purpose - are a "
               "cornerstone of cyber deception: because no benign user should ever "
               "touch them, every interaction is, by definition, suspicious [1], [2]. "
               "Medium-interaction honeypots such as Cowrie [3] emulate a Unix shell, "
               "enticing attackers to reveal their tooling and tradecraft while "
               "safely containing them. However, the dominant output of such systems "
               "is a log: a chronological record of commands that a human analyst "
               "must still read and interpret. At scale, this interpretation burden "
               "is the bottleneck.", "body0"))
    s.append(P("The gap we address is semantic: existing honeypots tell you what an "
               "attacker typed, but not why. Knowing that an attacker ran "
               "`cat /etc/shadow` followed by `wget http://.../x.sh` and then "
               "`rm -rf /var/log/auth.log` is far more actionable when the system "
               "recognises this as credential access -> execution -> defensive "
               "cleanup - a coherent attack progression - and raises a scored alert "
               "automatically."))
    s.append(P("This paper presents an intent-aware deception system that closes that "
               "gap in real time. Our contributions are:"))
    s += OL([
        "A 10-class, MITRE ATT&CK-aligned intent taxonomy for shell commands, with "
        "a deterministic mapping from each intent to an ATT&CK tactic/technique and "
        "to a kill-chain attack stage (Section IV).",
        "A hybrid classifier that arbitrates a deterministic rule engine, a "
        "calibrated ML core, and an optional LLM semantic layer by explicit "
        "confidence precedence, recording the deciding source for every event so "
        "that every classification is auditable (Section VI).",
        "An explainable additive risk-scoring engine (0-100) that combines "
        "per-intent weights with behavioural boosters and maps to four severity "
        "tiers with automatic alerting (Section VII).",
        "A complete, real-time, reproducible implementation - asynchronous capture "
        "pipeline, MongoDB persistence, FastAPI REST/WebSocket API, and a live React "
        "analyst dashboard - with the honeypot strictly isolated so no captured "
        "command is ever executed on the host or backend (Sections IX, XII).",
        "An honest experimental evaluation with leakage control and a stricter "
        "leave-families-out protocol, reporting both the favourable and the "
        "conservative numbers (Sections X-XI).",
    ])

    # ---- II. Related Work ----
    s.append(H1("II", "Related Work"))
    s.append(P("<b>Honeypots and deception.</b> Spitzner [1] and Provos and Holz [2] "
               "established honeypots as instruments for observing attacker "
               "behaviour; Cowrie [3] is the de-facto medium-interaction SSH/Telnet "
               "honeypot, emulating a shell and logging structured JSON events. These "
               "systems are excellent sensors but are typically paired with manual or "
               "signature-only analysis.", "body0"))
    s.append(P("<b>Command and intrusion classification.</b> Text-classification "
               "techniques over command lines and system logs are well established; "
               "TF-IDF vector-space representations [4] with linear classifiers such "
               "as support-vector machines [5] remain strong, interpretable baselines "
               "for short, high-dimensional sparse text. Character-n-gram features "
               "are known to be robust to the lexical variation and obfuscation "
               "typical of malicious inputs."))
    s.append(P("<b>Adversary modelling.</b> MITRE ATT&CK [6] provides a standard "
               "taxonomy of adversary tactics and techniques and has become the "
               "lingua franca for describing intrusions. Mapping observed behaviour "
               "onto ATT&CK tactics enables shared vocabulary and downstream "
               "automation."))
    s.append(P("<b>LLMs for security triage.</b> Recent work applies large language "
               "models to security-log summarisation and triage. LLMs offer strong "
               "semantic generalisation but introduce latency, cost, non-determinism, "
               "and availability dependencies - properties ill-suited to a mandatory "
               "real-time path."))
    s.append(P("<b>Our position.</b> Rather than choosing one paradigm, we fuse them: "
               "deterministic rules give precision and auditability on known "
               "signatures; a calibrated ML model gives generalisation and "
               "probabilistic confidence; and an LLM is an optional fallback for "
               "genuinely novel or ambiguous commands. The novelty is not any single "
               "classifier but the arbitration architecture and its integration into "
               "a real-time, explainable, end-to-end profiling system."))

    # ---- III. System Architecture ----
    s.append(H1("III", "System Architecture"))
    s.append(P("The system is a streaming pipeline from honeypot capture to analyst "
               "dashboard (Fig. 1).", "body0"))
    s.append(arch_drawing(FIG_W))
    s.append(P("<b>Data flow.</b> (1) The honeypot captures a login/command and "
               "appends a JSON event to its log. (2) An asynchronous collector tails "
               "the log and emits normalised events without blocking. (3) Feature "
               "extraction attaches session context (command counts, login failures, "
               "timing). (4) The hybrid classifier assigns an intent, a deciding "
               "source, and a confidence. (5) The attack-stage mapper places the "
               "intent on the kill chain; the risk engine scores the session; the "
               "profiler aggregates per-session and per-attacker state. (6) Everything "
               "is persisted to MongoDB and (7) exposed via a FastAPI REST + WebSocket "
               "API to (8) a live React dashboard."))
    s.append(P("<b>Design principles.</b> (i) ML is mandatory, the LLM is optional - "
               "the system starts and operates fully without any API key. (ii) Every "
               "decision is auditable - each event stores its deciding source and "
               "evidence. (iii) Strict isolation - the honeypot is the only component "
               "that touches attacker input, and it only emulates a shell."))

    # ---- IV. Intent Taxonomy ----
    s.append(H1("IV", "Intent Taxonomy and MITRE Mapping"))
    s.append(P("We define ten intent classes, each mapped deterministically to a "
               "MITRE ATT&CK tactic/technique and to a kill-chain attack stage. The "
               "mapping is a static table in code (`taxonomy.py`), so intent -> tactic "
               "-> stage is reproducible, not inferred.", "body0"))
    s.append(table(
        "Intent Taxonomy, MITRE ATT&CK Tactic, and Attack Stage",
        ["Intent class", "MITRE tactic", "Representative technique(s)", "Stage"],
        [
            ["RECONNAIS-<br/>SANCE", "Reconnaissance (TA0043)", "Active Scanning (T1595); Network Service Discovery (T1046)", "RECON"],
            ["DISCOVERY", "Discovery (TA0007)", "System Information (T1082); File/Dir Discovery (T1083); Process Discovery (T1057)", "DISCOVERY"],
            ["CREDENTIAL_<br/>ACCESS", "Credential Access (TA0006)", "OS Credential Dumping (T1003); Unsecured Credentials (T1552)", "CRED_<br/>ACCESS"],
            ["EXECUTION", "Execution (TA0002)", "Command & Scripting Interpreter (T1059)", "EXECUTION"],
            ["PRIVILEGE_<br/>ESCALATION", "Privilege Escalation (TA0004)", "Abuse Elevation Control (T1548); Exploitation for Priv-Esc (T1068)", "PRIV_ESC"],
            ["PERSISTENCE", "Persistence (TA0003)", "Account Manipulation (T1098); Scheduled Task (T1053); Create Account (T1136)", "PERSIST-<br/>ENCE"],
            ["EXPLOITATION", "Execution / Initial Access", "Exploit Public-Facing Application (T1190)", "EXECUTION"],
            ["EXFILTRATION", "Exfiltration (TA0010)", "Exfil over C2 (T1041); Exfil over Alt. Protocol (T1048)", "EXFIL"],
            ["CLEANUP", "Defense Evasion (TA0005)", "Indicator Removal - clear logs/history (T1070)", "CLEANUP"],
            ["OTHER", "-", "(no confident tactic)", "UNKNOWN"],
        ],
        widths=[25, 21, 37, 22], fs=6.2, wrap=True))
    s.append(P("Two deliberate choices: EXPLOITATION maps to the EXECUTION stage (an "
               "exploit is a means of code execution), and OTHER maps to UNKNOWN (we "
               "do not force a kill-chain position onto unclassified input).", "body0"))

    # ---- V. ML Methodology ----
    s.append(H1("V", "Machine-Learning Methodology"))
    s.append(H2("A", "Task"))
    s.append(P("Supervised multi-class classification of a single shell-command "
               "string into one of the ten intent classes. The classifier consumes "
               "only the raw command text; behavioural session features are reserved "
               "for the risk engine (Section VII).", "body0"))
    s.append(H2("B", "Dataset"))
    s.append(P("The corpus is generated programmatically from 242 curated command "
               "template families. Each family declares an intent and a parameterised "
               "template; templates are expanded by substituting from value pools "
               "(IPs, ports, paths, payload names, CVE IDs), capped at 14 variants per "
               "family, then de-duplicated. After removing 5 exact duplicates the "
               "final corpus is 1360 unique commands across 10 classes (Table II). "
               "Labels are assigned by construction, and the `family_id` is retained "
               "as a group key for the robustness split.", "body0"))
    s.append(table(
        "Class Distribution (samples / families)",
        ["Intent", "Samples", "Families"],
        [["RECONNAISSANCE", "80", "28"], ["DISCOVERY", "134", "35"],
         ["CREDENTIAL_ACCESS", "121", "27"], ["EXECUTION", "318", "24"],
         ["PRIVILEGE_ESCALATION", "57", "30"], ["PERSISTENCE", "162", "20"],
         ["EXPLOITATION", "100", "18"], ["EXFILTRATION", "184", "18"],
         ["CLEANUP", "87", "18"], ["OTHER", "117", "24"],
         ["Total", "1360", "242"]],
        widths=[46, 24, 24], aligns=["LEFT", "RIGHT", "RIGHT"], fs=7.2,
        bold_last=True))
    s.append(svg_fig("dataset_distribution.svg",
                     "Class distribution of the 1360-command corpus across the ten "
                     "MITRE-aligned intent classes."))
    s.append(H2("C", "Features"))
    s.append(P("A scikit-learn `FeatureUnion` of two TF-IDF representations: a word "
               "vectoriser (analyzer=word, whitespace tokenisation, n-grams (1,2), "
               "sublinear_tf) and a character vectoriser (analyzer=char_wb, n-grams "
               "(3,6), sublinear_tf). The whitespace tokeniser keeps flags, paths, and "
               "URLs intact (`-O`, `/etc/shadow`), and the character n-grams capture "
               "sub-token cues (flag fragments, path fragments, obfuscation) that a "
               "word-only model misses - the single most important design choice for "
               "the shell-command domain.", "body0"))
    s.append(H2("D", "Model selection"))
    s.append(P("Three candidates over the identical feature space were compared by "
               "4-fold stratified cross-validation on the training split only, "
               "scoring macro-F1 (Table III). The winner is a calibrated linear SVM: "
               "`LinearSVC(C=1.0, class_weight=balanced)` wrapped in "
               "`CalibratedClassifierCV(method=sigmoid, cv=3)`. Calibration (Platt "
               "scaling [7]) converts SVM margins into probabilities that the runtime "
               "hybrid layer thresholds on.", "body0"))
    s.append(table(
        "Model Selection (4-fold CV macro-F1, training split)",
        ["Candidate", "Estimator", "CV macro-F1"],
        [["linsvc_calibrated (selected)", "Calibrated LinearSVC", "0.8539 +/- 0.018"],
         ["logreg", "LogisticRegression (C=3.0)", "0.8482 +/- 0.017"],
         ["complement_nb", "ComplementNB (alpha=0.3)", "0.8146 +/- 0.028"]],
        widths=[34, 40, 26], aligns=["LEFT", "LEFT", "RIGHT"], fs=6.9))
    s.append(H2("E", "Protocol and leakage control"))
    s.append(P("A stratified 80/20 split (1088 train / 272 test, "
               "random_state=1337). The code asserts that no identical command string "
               "appears in both train and test - this leakage control is why the "
               "headline accuracy is a realistic 94%, not an inflated 100%. The "
               "shipped artefact is refit on all 1360 samples and serialised with "
               "metadata; loading is lazy and degrades gracefully to rules+LLM if the "
               "artefact is absent.", "body0"))

    # ---- VI. Hybrid Classification ----
    s.append(H1("VI", "Hybrid Classification"))
    s.append(P("At inference, three sources are arbitrated by explicit confidence "
               "precedence (`hybrid_classifier.py`):", "body0"))
    s += OL([
        "<b>Strong RULE:</b> rule confidence >= 0.90 and label != OTHER -> source RULE.",
        "<b>Confident ML:</b> calibrated ML probability >= 0.40 -> source ML "
        "(HYBRID if the rule agrees).",
        "<b>Gemini (opt.):</b> consulted only when 1 and 2 are inconclusive -> "
        "source GEMINI.",
        "<b>Best-available:</b> highest-confidence non-OTHER among rule/ML.",
        "<b>Fallback:</b> nothing confident (>= 0.10) -> OTHER, source FALLBACK.",
    ])
    s += UL([
        "The rule engine comprises 13 rules over 43 curated regular-expression "
        "patterns, each with an attached confidence; a strong (>=0.90) non-OTHER "
        "match is authoritative - deterministic, instant, and auditable.",
        "The ML core decides when no strong rule fires but its calibrated "
        "probability is >= 0.40; when the rule agrees with the ML label the event is "
        "recorded as HYBRID, otherwise ML.",
        "Gemini (`gemini-2.5-flash`) is consulted only when neither rule nor ML is "
        "decisive. Its output is gated (accepted at >=0.85) and its input sanitised. "
        "It is never on the hot path for known attacks, and the system runs fully "
        "without it.",
        "Every event stores its deciding source (RULE/ML/HYBRID/GEMINI/FALLBACK) and, "
        "for ML/HYBRID, the calibrated confidence - surfaced on the dashboard so no "
        "decision is a black box.",
    ])
    s.append(P("This arbitration is the core systems contribution: it combines the "
               "precision and auditability of rules, the generalisation and calibrated "
               "confidence of ML, and the semantic reach of an LLM, while keeping ML "
               "mandatory and the LLM optional."))

    # ---- VII. Risk Scoring ----
    s.append(H1("VII", "Explainable Risk Scoring"))
    s.append(P("Each session receives an integer risk score in [0, 100] from an "
               "additive engine (`risk_engine.py`): a base weight for the "
               "highest-severity observed intent, plus behavioural boosters derived "
               "from session context, clamped to 100.", "body0"))
    s.append(table(
        "Base Intent Weights",
        ["Intent", "Weight"],
        [["OTHER", "0"], ["RECONNAISSANCE", "10"], ["DISCOVERY", "15"],
         ["CLEANUP", "15"], ["EXECUTION", "20"], ["CREDENTIAL_ACCESS", "25"],
         ["PRIVILEGE_ESCALATION", "30"], ["PERSISTENCE", "30"],
         ["EXPLOITATION", "30"], ["EXFILTRATION", "35"]],
        widths=[60, 22], aligns=["LEFT", "RIGHT"], fs=7.2))
    s.append(table(
        "Behavioural Boosters",
        ["Condition", "Points"],
        [["Any failed authentication", "+5"],
         ["Brute-force pattern (>= 3 failed logins)", "+10"],
         ["Rapid command bursts (high command rate)", "+5"],
         ["Deep session (>= 5 commands)", "+5"],
         ["High intent variety (>= 4 distinct intents)", "+5"]],
        widths=[64, 20], aligns=["LEFT", "RIGHT"], fs=7.2))
    s.append(P("The score maps to four severity tiers - LOW 0-24, MEDIUM 25-49, HIGH "
               "50-74, CRITICAL 75-100 - and a session reaching >= 75 raises an "
               "automatic alert. Because the formula is additive and transparent, "
               "every score is fully explainable.", "body0"))

    # ---- VIII. Attacker Profiling ----
    s.append(H1("VIII", "Attacker Profiling"))
    s.append(P("The profiler maintains two aggregation levels. A session profile "
               "records the intent sequence, dominant intent, furthest attack stage, "
               "command/login counts, duration, risk score, and severity - assembling "
               "isolated events into a multi-stage trajectory (e.g. reconnaissance -> "
               "discovery -> credential-access -> privilege-escalation -> exfiltration "
               "-> cleanup). An attacker profile aggregates all sessions from one "
               "source IP: total sessions/events, peak and average risk, dominant "
               "intent, and first/last-seen timestamps - answering whether a host is a "
               "one-off scanner or a persistent, escalating threat.", "body0"))

    # ---- IX. Implementation ----
    s.append(H1("IX", "Implementation"))
    s.append(P("<b>Backend.</b> Python 3.13, FastAPI, Motor (async MongoDB). The "
               "capture->classify->score->persist path is fully asynchronous so "
               "ingestion never blocks. The REST/WebSocket surface includes health, "
               "dashboard statistics, events, sessions (with on-demand MITRE mapping "
               "and optional Gemini analysis), attackers, alerts, and six analytics "
               "endpoints, plus `/ws/events` and `/ws/alerts` for live streaming.",
               "body0"))
    s.append(P("<b>Frontend.</b> A React 19 + Vite + Tailwind + Recharts single-page "
               "analyst dashboard with five sections - Overview, Live Sessions, "
               "Attacker Profiles, Threat Alerts, Analytics. Each event row shows an "
               "intent badge, severity, and a classification-source badge (with ML "
               "confidence), realising the explainable goal on screen."))
    s.append(P("<b>Deployment and reproducibility.</b> The full stack - MongoDB, "
               "Cowrie, API, and dashboard - is containerised via Docker Compose and "
               "starts with a single command. A fixed RANDOM_SEED = 1337 and pinned "
               "scientific-stack versions (scikit-learn 1.9.0, numpy 2.5.2) make "
               "training and evaluation deterministic and reproducible."))

    # ---- X. Experimental Evaluation ----
    s.append(H1("X", "Experimental Evaluation"))
    s.append(H2("A", "Primary evaluation (leakage-controlled held-out set)"))
    s.append(P("On the 272-command held-out test set the calibrated linear SVM "
               "achieves the metrics in Table VI, with per-class results in Table VII. "
               "The confusion matrix (Fig. 3) and per-class F1 scores (Fig. 4) "
               "visualise where the model is strong and where intents overlap.",
               "body0"))
    s.append(table(
        "Held-out Performance (272 test commands)",
        ["Metric", "Value"],
        [["Accuracy", "94.49%"], ["Macro Precision", "0.9367"],
         ["Macro Recall", "0.9158"], ["Macro F1", "0.9229"],
         ["Weighted F1", "0.9436"]],
        widths=[60, 24], aligns=["LEFT", "RIGHT"], fs=7.4))
    s.append(table(
        "Per-class Results (held-out)",
        ["Intent", "Prec.", "Recall", "F1", "Supp."],
        [["CLEANUP", "1.000", "0.941", "0.970", "17"],
         ["CREDENTIAL_ACCESS", "0.828", "1.000", "0.906", "24"],
         ["DISCOVERY", "0.828", "0.889", "0.857", "27"],
         ["EXECUTION", "1.000", "1.000", "1.000", "64"],
         ["EXFILTRATION", "1.000", "1.000", "1.000", "37"],
         ["EXPLOITATION", "1.000", "1.000", "1.000", "20"],
         ["OTHER", "0.909", "0.870", "0.889", "23"],
         ["PERSISTENCE", "0.970", "1.000", "0.985", "32"],
         ["PRIVILEGE_ESCALATION", "1.000", "0.833", "0.909", "12"],
         ["RECONNAISSANCE", "0.833", "0.625", "0.714", "16"]],
        widths=[40, 16, 16, 16, 14],
        aligns=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"], fs=6.9))
    s.append(svg_fig("confusion_matrix.svg",
                     "Held-out confusion matrix (272 commands). Errors stay within "
                     "neighbouring intents; none crosses into an unrelated tactic."))
    s.append(svg_fig("per_class_f1.svg",
                     "Per-class F1 on the held-out set. EXECUTION, EXFILTRATION, and "
                     "EXPLOITATION reach perfect F1; RECONNAISSANCE is weakest."))
    s.append(H2("B", "Robustness evaluation (leave-families-out)"))
    s.append(P("To test generalisation to unseen command templates, we hold out whole "
               "families so that no test template appears in training (Table VIII, "
               "Fig. 5). This is a much harder test and the score is lower by design.",
               "body0"))
    s.append(table(
        "Primary vs. Robustness Evaluation",
        ["Protocol", "Acc.", "Macro-F1", "Train/Test"],
        [["Primary (stratified, leakage-ctl.)", "94.49%", "0.9229", "1088/272"],
         ["Robustness (leave-families-out)", "67.87%", "0.5267", "1055/305"]],
        widths=[42, 16, 18, 20],
        aligns=["LEFT", "RIGHT", "RIGHT", "RIGHT"], fs=6.9))
    s.append(svg_fig("primary_vs_robustness.svg",
                     "Primary vs. leave-families-out accuracy and macro-F1. The gap "
                     "quantifies the lexical model's generalisation limit and "
                     "motivates the hybrid design."))
    s.append(H2("C", "End-to-end live verification"))
    s.append(P("Beyond offline metrics, an end-to-end script drives all ten intents "
               "through the running system and a verifier confirms each captured "
               "command carries a classification source and, for ML/HYBRID, a real "
               "calibrated confidence - demonstrating the ML core is genuinely in the "
               "live pipeline, not merely evaluated offline.", "body0"))

    # ---- XI. Results and Discussion ----
    s.append(H1("XI", "Results and Discussion"))
    s.append(P("The model classifies attacker intent with 94.49% held-out accuracy "
               "and a balanced 0.9229 macro-F1, confirming that lexical features "
               "capture intent well for the majority of commands. Three classes - "
               "EXECUTION, EXFILTRATION, EXPLOITATION - reach perfect held-out F1, "
               "reflecting their highly distinctive vocabulary.", "body0"))
    s.append(P("The weakest class is RECONNAISSANCE (F1 0.714): short probes such as "
               "`whoami`, `id`, and `uname` overlap lexically with DISCOVERY and "
               "CREDENTIAL_ACCESS, and it is the smallest test class (support 16). "
               "Crucially, the confusion matrix shows errors stay within neighbouring "
               "intents - no misclassification crosses into an unrelated tactic - so "
               "mistakes rarely change the kill-chain interpretation. This ambiguous "
               "boundary is exactly what the rule and optional-LLM layers exist to "
               "disambiguate at runtime."))
    s.append(P("The leave-families-out result (67.87%) is the honest headline for "
               "novel templates. A purely lexical model cannot fully generalise to "
               "command shapes it has never seen; we report this openly rather than "
               "quoting only the favourable split. It directly motivates the hybrid "
               "design: deterministic rules cover known-signature novelty, and the "
               "optional semantic LLM layer handles genuinely new commands - so the "
               "system's real-world robustness exceeds that of the ML core in "
               "isolation."))
    s.append(P("Finally, the architecture delivers explainability end-to-end: every "
               "event exposes its deciding source and evidence, and every risk score "
               "decomposes into transparent additive terms. An analyst can always "
               "answer 'why was this flagged?'"))

    # ---- XII. Limitations & Ethics ----
    s.append(H1("XII", "Limitations and Ethical / Safety Considerations"))
    s.append(P("<b>Limitations.</b> (1) The training corpus, though realistic and "
               "family-diverse, is generated from curated templates rather than "
               "harvested from a live production honeypot; the leave-families-out "
               "result quantifies the resulting generalisation gap. (2) The classifier "
               "operates per command; richer sequence models could exploit "
               "inter-command context further. (3) Small classes (RECONNAISSANCE, "
               "PRIVILEGE_ESCALATION) have modest support.", "body0"))
    s.append(P("<b>Safety and ethics.</b> The honeypot is strictly isolated and only "
               "emulates a shell - no captured attacker command is ever executed on "
               "the host or backend. All demonstration attacks use RFC-5737 "
               "documentation IP ranges (192.0.2.0/24, 198.51.100.0/24) that route "
               "nowhere, and no real malicious payloads are run. Secrets are confined "
               "to an untracked `.env`. The system is a defensive research tool and "
               "should only be deployed against infrastructure one owns."))

    # ---- XIII. Conclusion ----
    s.append(H1("XIII", "Conclusion and Future Work"))
    s.append(P("We presented an intent-aware deception system that converts raw "
               "honeypot command streams into real-time, explainable attacker "
               "profiles. By fusing a deterministic rule engine, a calibrated ML core "
               "(94.49% held-out accuracy, 0.9229 macro-F1), and an optional LLM "
               "semantic layer under explicit confidence arbitration - and by scoring "
               "each session with a transparent additive risk engine - the system "
               "infers why an attacker acts, assembles multi-stage trajectories, and "
               "raises scored alerts, all while keeping ML mandatory, the LLM optional, "
               "and every decision auditable. We deliberately report a stricter "
               "leave-families-out score (67.87%) to characterise generalisation "
               "honestly.", "body0"))
    s.append(P("<b>Future work.</b> (1) Harvest and incorporate live honeypot traffic "
               "to close the template-generalisation gap. (2) Add sequence-aware "
               "modelling over the command stream. (3) Expand the rule/pattern library "
               "and intent taxonomy. (4) Study adversarial robustness to command "
               "obfuscation. (5) Explore automated adaptive deception - having the "
               "honeypot respond differently based on inferred intent."))

    # ---- References ----
    s.append(H1("", "References"))
    refs = [
        "L. Spitzner, Honeypots: Tracking Hackers. Boston, MA, USA: Addison-Wesley, 2002.",
        "N. Provos and T. Holz, Virtual Honeypots: From Botnet Tracking to Intrusion "
        "Detection. Upper Saddle River, NJ, USA: Addison-Wesley, 2007.",
        "M. Oosterhof, \"Cowrie SSH/Telnet Honeypot,\" 2016-. [Online]. Available: "
        "https://github.com/cowrie/cowrie",
        "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text "
        "retrieval,\" Inf. Process. Manage., vol. 24, no. 5, pp. 513-523, 1988.",
        "T. Joachims, \"Text categorization with support vector machines,\" in Proc. "
        "European Conf. Machine Learning (ECML), 1998, pp. 137-142.",
        "B. E. Strom et al., \"MITRE ATT&CK: Design and philosophy,\" The MITRE Corp., "
        "Tech. Rep., 2020. [Online]. Available: https://attack.mitre.org",
        "J. Platt, \"Probabilistic outputs for support vector machines,\" in Advances "
        "in Large Margin Classifiers, MIT Press, 1999, pp. 61-74.",
        "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. "
        "Learn. Res., vol. 12, pp. 2825-2830, 2011.",
        "S. Ramirez, \"FastAPI,\" 2018-. [Online]. Available: https://fastapi.tiangolo.com",
        "E. M. Hutchins, M. J. Cloppert, and R. M. Amin, \"Intelligence-driven "
        "computer network defense informed by analysis of adversary campaigns and "
        "intrusion kill chains,\" in Proc. 6th Int. Conf. Information Warfare and "
        "Security, 2011, pp. 113-125.",
    ]
    for i, r in enumerate(refs, 1):
        s.append(Paragraph(f"[{i}]&nbsp;&nbsp;{md(r)}", S["ref"]))

    doc.build(s)
    kb = OUT.stat().st_size / 1024
    print(f"[ok] {OUT.relative_to(ROOT)}  ({kb:.0f} KB, {_FIG[0]} figures)")


if __name__ == "__main__":
    build()
