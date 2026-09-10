#!/usr/bin/env python3
"""
Render the project's Markdown documentation to clean, printable PDFs.

Pure-Python toolchain (no system binaries): `markdown` -> HTML -> `xhtml2pdf`.
Every PDF is generated from the Markdown source; nothing is hand-edited.

Usage:
    .venv/Scripts/python.exe scripts/build_docs_pdf.py
Outputs into docs/pdf/.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "pdf"

# (markdown source, output pdf name, cover title)
DOCS = [
    ("docs/VSCODE_RUN_GUIDE.md",      "0_How_To_Run_In_VSCode.pdf",    "How to Run in VS Code — Step by Step (+ AI Setup)"),
    ("docs/IEEE_PAPER_SOURCE.md",     "1_IEEE_Paper_Source.pdf",       "Intent-Aware Deception System — IEEE Paper Source"),
    ("docs/DASHBOARD_GUIDE.md",       "2_Dashboard_Guide.pdf",         "Dashboard Guide — Every Section Explained"),
    ("docs/ML_MODEL_ANALYSIS.md",     "3_ML_Model_Analysis.pdf",       "Machine Learning — Model & Evaluation Analysis"),
    ("docs/RUN_AND_ATTACK_GUIDE.md",  "4_Run_and_Attack_Guide.pdf",    "Run & Attack Guide"),
    # Bonus: the honest final report and raw evaluation, as PDFs too.
    ("docs/FINAL_REPORT.md",          "5_Final_Report.pdf",            "Final Implementation Report"),
    ("docs/evaluation/evaluation_report.md", "6_Evaluation_Report.pdf", "Experimental Evaluation"),
    ("docs/PANEL_VIVA_PREP.md",       "7_Panel_Viva_Prep.pdf",         "Panel Viva Preparation — Anticipated Questions & Answers"),
]

# xhtml2pdf renders with built-in Helvetica/Courier which have no emoji glyphs.
# Replace the symbols we actually use with ASCII, then strip any remaining
# pictographs so nothing renders as a tofu box. (Markdown sources keep their glyphs.)
_SYMBOL_MAP = {
    "▶": "»", "✔": "[ok]", "️": "", "✅": "[done]",
    "❌": "[x]", "\U0001f7e1": "[~]", "→": "->", "←": "<-",
    "≥": ">=", "≤": "<=", "×": "x", "–": "-", "—": "--",
    "‘": "'", "’": "'", "“": '"', "”": '"', "…": "...",
    "±": "+/-", "∑": "sum", "·": "-",
}
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF]",
    flags=re.UNICODE,
)


def sanitize(text: str) -> str:
    for bad, good in _SYMBOL_MAP.items():
        text = text.replace(bad, good)
    return _EMOJI_RE.sub("", text)


CSS = """
@page { size: a4; margin: 1.8cm 1.6cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5px; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 21px; color: #0b3d91; border-bottom: 2px solid #0b3d91; padding-bottom: 4px; margin-top: 6px; }
h2 { font-size: 16px; color: #0b3d91; border-bottom: 1px solid #c8d4ea; padding-bottom: 2px; margin-top: 16px; }
h3 { font-size: 13px; color: #12306b; margin-top: 12px; }
h4 { font-size: 11.5px; color: #333; margin-top: 10px; }
p { margin: 5px 0; }
a { color: #0b3d91; text-decoration: none; }
strong { color: #111; }
code { font-family: Courier, monospace; font-size: 9.5px; background: #eef1f6; padding: 1px 3px; }
pre { font-family: Courier, monospace; font-size: 9px; background: #f4f6fa; border: 1px solid #d8dee8;
      padding: 7px 9px; margin: 7px 0; -pdf-keep-in-frame-mode: shrink; white-space: pre-wrap; word-wrap: break-word; }
pre code { background: transparent; padding: 0; font-size: 9px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th { background: #0b3d91; color: #fff; border: 1px solid #0b3d91; padding: 3px 5px; text-align: left; font-size: 9px; }
td { border: 1px solid #c4cede; padding: 3px 5px; font-size: 9px; vertical-align: top; word-wrap: break-word; word-break: break-word; }
tr:nth-child(even) td { background: #f4f6fa; }
blockquote { border-left: 3px solid #0b3d91; background: #f4f6fa; margin: 8px 0; padding: 5px 10px; color: #333; }
ul, ol { margin: 5px 0 5px 8px; }
li { margin: 2px 0; }
hr { border: none; border-top: 1px solid #c8d4ea; margin: 12px 0; }
.cover { color: #0b3d91; font-size: 24px; font-weight: bold; margin-bottom: 2px; }
.cover-sub { color: #555; font-size: 11px; margin-bottom: 14px; }
"""

MD_EXT = ["tables", "fenced_code", "sane_lists", "toc", "attr_list", "def_list"]


def build_one(src_rel: str, out_name: str, title: str) -> bool:
    src = ROOT / src_rel
    if not src.exists():
        print(f"  [skip] {src_rel} (not found)")
        return False
    raw = sanitize(src.read_text(encoding="utf-8"))
    body = markdown.markdown(raw, extensions=MD_EXT)
    cover = (f'<div class="cover">{sanitize(title)}</div>'
             f'<div class="cover-sub">Intent-Aware Deception System for Real-Time Attacker Profiling'
             f' &ndash; generated from {src_rel}</div><hr/>')
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>{cover}{body}</body></html>")
    out = OUT_DIR / out_name
    with open(out, "wb") as fh:
        result = pisa.CreatePDF(html, dest=fh, encoding="utf-8")
    if result.err:
        print(f"  [FAIL] {out_name} ({result.err} errors)")
        return False
    kb = out.stat().st_size / 1024
    print(f"  [ok]   {out_name}  ({kb:.0f} KB)")
    return True


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering PDFs into {OUT_DIR} ...")
    ok = 0
    for src_rel, out_name, title in DOCS:
        if build_one(src_rel, out_name, title):
            ok += 1
    print(f"\nDone: {ok}/{len(DOCS)} PDFs generated in docs/pdf/")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
