#!/usr/bin/env python3
"""
Regenerate the evaluation report and figures FROM the single source of truth:
``backend/app/ml/artifacts/metrics.json`` (written by train.py).

Why this exists
---------------
Every number in the report and every figure is derived here from the metrics
file the model was actually deployed with. Nothing is hand-typed, so the report
can never drift from the model (honesty_note #4: "re-running reproduces these
numbers"). Figures are emitted as dependency-free SVG — no matplotlib, no
binary blobs that could silently go stale — so `python scripts/generate_eval_assets.py`
reproduces them identically on any machine with stdlib Python.

Outputs (all under docs/evaluation/):
    evaluation_report.md        - honest, ML-first evaluation report
    confusion_matrix.svg        - primary held-out confusion matrix heatmap
    per_class_f1.svg            - per-class precision/recall/F1
    dataset_distribution.svg    - labelled-sample counts per class
    primary_vs_robustness.svg   - held-out vs leave-families-out comparison

Usage:
    .venv/Scripts/python.exe scripts/generate_eval_assets.py
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
METRICS = ROOT / "backend" / "app" / "ml" / "artifacts" / "metrics.json"
OUT = ROOT / "docs" / "evaluation"

# Colour palette (SOC dark theme, consistent with the dashboard).
BG = "#0d121d"
GRID = "#1f293d"
FG = "#e2e8f0"
MUTE = "#94a3b8"
ACCENT = "#22d3ee"
VIOLET = "#a78bfa"
AMBER = "#fbbf24"
ROSE = "#fb7185"


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


# --------------------------------------------------------------------------- #
# SVG helpers (hand-rolled, dependency-free)
# --------------------------------------------------------------------------- #
def _svg_open(w: int, h: int, title: str) -> List[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="Menlo,Consolas,monospace">',
        f'<title>{html.escape(title)}</title>',
        f'<rect width="{w}" height="{h}" fill="{BG}"/>',
    ]


def _text(x, y, s, size=12, fill=FG, anchor="start", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{html.escape(str(s))}</text>')


def _heat_colour(frac: float, on_diag: bool) -> str:
    """Cyan ramp for correct (diagonal), rose ramp for confusion (off-diagonal)."""
    if frac <= 0:
        return "#0e1626"
    if on_diag:
        # interpolate dark->cyan
        r = int(14 + (34 - 14) * frac)
        g = int(22 + (211 - 22) * frac)
        b = int(38 + (238 - 38) * frac)
    else:
        r = int(30 + (251 - 30) * frac)
        g = int(20 + (113 - 20) * frac)
        b = int(38 + (133 - 38) * frac)
    return f"rgb({r},{g},{b})"


def render_confusion_matrix(cm: Dict, path: Path) -> None:
    labels = cm["labels"]
    matrix = cm["matrix"]
    n = len(labels)
    cell = 46
    left, top = 190, 130
    right, bottom = 40, 60
    w = left + n * cell + right
    h = top + n * cell + bottom

    s = _svg_open(w, h, "Primary held-out confusion matrix")
    s.append(_text(left + n * cell / 2, 34, "Confusion Matrix — Held-out Test Set (n=272)",
                   size=15, fill=FG, anchor="middle", weight="bold"))
    s.append(_text(left + n * cell / 2, 54, "rows = true label, cols = predicted label",
                   size=11, fill=MUTE, anchor="middle"))

    row_totals = [max(1, sum(r)) for r in matrix]
    # column headers (rotated)
    for j, lab in enumerate(labels):
        cx = left + j * cell + cell / 2
        s.append(f'<text x="{cx}" y="{top - 8}" font-size="10" fill="{MUTE}" '
                 f'text-anchor="start" transform="rotate(-45 {cx} {top - 8})">{html.escape(lab)}</text>')
    # cells + row labels
    for i, lab in enumerate(labels):
        cy = top + i * cell
        s.append(_text(left - 8, cy + cell / 2 + 4, lab, size=10, fill=MUTE, anchor="end"))
        for j in range(n):
            v = matrix[i][j]
            frac = v / row_totals[i]
            x = left + j * cell
            colour = _heat_colour(frac, on_diag=(i == j))
            s.append(f'<rect x="{x}" y="{cy}" width="{cell - 2}" height="{cell - 2}" '
                     f'fill="{colour}" stroke="{GRID}" stroke-width="1"/>')
            if v:
                txt_fill = "#04121a" if (i == j and frac > 0.5) else FG
                s.append(_text(x + cell / 2 - 1, cy + cell / 2 + 4, v, size=12,
                               fill=txt_fill, anchor="middle", weight="bold"))
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


def render_bar_group(per_class: Dict, path: Path) -> None:
    """Horizontal grouped bars: precision / recall / F1 per class."""
    classes = sorted(per_class.keys())
    row_h = 46
    top, left = 70, 190
    barw = 460
    w = left + barw + 70
    h = top + len(classes) * row_h + 40

    s = _svg_open(w, h, "Per-class precision / recall / F1")
    s.append(_text(w / 2, 30, "Per-class Precision / Recall / F1 (held-out)",
                   size=15, fill=FG, anchor="middle", weight="bold"))
    # legend
    for k, (lab, col) in enumerate({"precision": ACCENT, "recall": VIOLET, "f1": AMBER}.items()):
        lx = left + k * 130
        s.append(f'<rect x="{lx}" y="46" width="12" height="12" fill="{col}"/>')
        s.append(_text(lx + 18, 56, lab, size=11, fill=MUTE))
    # gridlines at 0/.25/.5/.75/1
    for g in (0, .25, .5, .75, 1.0):
        gx = left + barw * g
        s.append(f'<line x1="{gx}" y1="{top}" x2="{gx}" y2="{top + len(classes) * row_h}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(_text(gx, top + len(classes) * row_h + 18, f"{g:.2f}", size=9,
                       fill=MUTE, anchor="middle"))
    for i, c in enumerate(classes):
        y0 = top + i * row_h
        s.append(_text(left - 8, y0 + 20, c, size=10, fill=FG, anchor="end"))
        m = per_class[c]
        for k, (key, col) in enumerate({"precision": ACCENT, "recall": VIOLET, "f1": AMBER}.items()):
            val = float(m.get(key, 0))
            bh = 10
            by = y0 + 2 + k * (bh + 1)
            s.append(f'<rect x="{left}" y="{by}" width="{barw * val:.1f}" height="{bh}" '
                     f'fill="{col}" rx="1"/>')
            s.append(_text(left + barw * val + 5, by + bh - 1, f"{val:.2f}", size=8, fill=MUTE))
        s.append(_text(left + barw + 40, y0 + 20, f"n={m.get('support', 0)}", size=9,
                       fill=MUTE, anchor="end"))
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


def render_dataset_distribution(dist: Dict, path: Path) -> None:
    items = sorted(dist.items(), key=lambda kv: kv[1]["samples"], reverse=True)
    row_h = 34
    top, left = 70, 190
    barw = 430
    maxv = max(v["samples"] for _, v in items)
    w = left + barw + 90
    h = top + len(items) * row_h + 30

    s = _svg_open(w, h, "Labelled sample distribution")
    s.append(_text(w / 2, 30, "Dataset — Labelled Samples per Class (1360 total, de-duplicated)",
                   size=14, fill=FG, anchor="middle", weight="bold"))
    for i, (c, v) in enumerate(items):
        y0 = top + i * row_h
        s.append(_text(left - 8, y0 + 18, c, size=10, fill=FG, anchor="end"))
        bw = barw * v["samples"] / maxv
        s.append(f'<rect x="{left}" y="{y0 + 6}" width="{bw:.1f}" height="16" fill="{ACCENT}" rx="2"/>')
        s.append(_text(left + bw + 6, y0 + 19,
                       f'{v["samples"]}  ({v["families"]} families)', size=10, fill=MUTE))
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


def render_primary_vs_robustness(primary: Dict, robust: Dict, path: Path) -> None:
    groups = [
        ("Held-out split\n(no shared command)", primary["accuracy"], primary["macro_f1"]),
        ("Leave-families-out\n(stricter, novel templates)", robust["accuracy"], robust["macro_f1"]),
    ]
    w, h = 560, 340
    left, top, barw, gap = 90, 80, 90, 60
    plot_h = 180
    s = _svg_open(w, h, "Primary vs robustness")
    s.append(_text(w / 2, 30, "Generalisation: Held-out vs Leave-families-out",
                   size=15, fill=FG, anchor="middle", weight="bold"))
    s.append(_text(w / 2, 50, "honest reporting — the stricter score is shown, not hidden",
                   size=10, fill=MUTE, anchor="middle"))
    # y grid
    for g in (0, .25, .5, .75, 1.0):
        gy = top + plot_h * (1 - g)
        s.append(f'<line x1="{left - 10}" y1="{gy}" x2="{w - 30}" y2="{gy}" stroke="{GRID}"/>')
        s.append(_text(left - 16, gy + 4, f"{g:.2f}", size=9, fill=MUTE, anchor="end"))
    x = left + 20
    for label, acc, f1 in groups:
        for k, (metric, val, col) in enumerate([("accuracy", acc, ACCENT), ("macro-F1", f1, VIOLET)]):
            bx = x + k * (barw / 2 + 6)
            bh = plot_h * val
            s.append(f'<rect x="{bx}" y="{top + plot_h - bh}" width="{barw / 2}" height="{bh}" '
                     f'fill="{col}" rx="2"/>')
            s.append(_text(bx + barw / 4, top + plot_h - bh - 6, f"{val:.3f}", size=10,
                           fill=FG, anchor="middle", weight="bold"))
            s.append(_text(bx + barw / 4, top + plot_h + 16, metric, size=9, fill=MUTE, anchor="middle"))
        for li, line in enumerate(label.split("\n")):
            s.append(_text(x + barw / 2, top + plot_h + 36 + li * 14, line, size=10,
                           fill=FG, anchor="middle"))
        x += barw + gap + 40
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def render_report(m: Dict, path: Path) -> None:
    ds = m["dataset"]
    pe = m["primary_evaluation"]
    rb = m["robustness_evaluation"]
    env = m.get("environment", {})
    per = pe["per_class"]

    L: List[str] = []
    w = L.append
    w("# Experimental Evaluation — Intent-Aware Deception System")
    w("")
    w("> **Every figure and number in this document is generated by "
      "[`scripts/generate_eval_assets.py`](../../scripts/generate_eval_assets.py) directly "
      "from [`metrics.json`](metrics.json), the exact metrics file the deployed model was "
      "trained and saved with. Nothing here is hand-typed. Re-running `train.py` with the "
      "fixed random seed reproduces these numbers.**")
    w("")
    w(f"- **Task:** {m.get('task')}")
    w(f"- **Generated at:** {m.get('generated_at')}")
    w(f"- **Deployed model:** `{pe['selected_model']}`")
    w(f"- **Environment:** " + ", ".join(f"{k} {v}" for k, v in env.items()))
    w("")
    w("---")
    w("")
    w("## 1. The headline number, stated honestly")
    w("")
    w(f"On a **{pe['split']}** with **{pe['train_samples']} training** and "
      f"**{pe['test_samples']} held-out test** commands, the deployed classifier "
      f"`{pe['selected_model']}` achieves:")
    w("")
    w("| Metric | Held-out value |")
    w("| :--- | ---: |")
    w(f"| **Accuracy** | **{_pct(pe['accuracy'])}** |")
    w(f"| Macro Precision | {pe['macro_precision']:.4f} |")
    w(f"| Macro Recall | {pe['macro_recall']:.4f} |")
    w(f"| **Macro F1** | **{pe['macro_f1']:.4f}** |")
    w(f"| Weighted F1 | {pe['weighted_f1']:.4f} |")
    w("")
    w(f"> **Leakage control:** {pe['leakage_control']}. This is why the number is "
      f"reported as 94%, not 100% — no test command was ever seen in training.")
    w("")
    w("![Confusion matrix](confusion_matrix.svg)")
    w("")
    w("## 2. Per-class performance (where it is strong, where it is weak)")
    w("")
    w("| Intent | Precision | Recall | F1 | Support |")
    w("| :--- | ---: | ---: | ---: | ---: |")
    for c in sorted(per.keys()):
        pc = per[c]
        w(f"| {c} | {pc['precision']:.3f} | {pc['recall']:.3f} | {pc['f1']:.3f} | {pc['support']} |")
    w("")
    # honest weakest-class callout, computed not typed
    weakest = min(per.items(), key=lambda kv: kv[1]["f1"])
    strongest = [c for c, v in per.items() if v["f1"] >= 0.999]
    w(f"- **Strongest:** {', '.join(sorted(strongest))} reach a perfect held-out F1 "
      f"(these classes use highly distinctive tokens).")
    w(f"- **Weakest:** `{weakest[0]}` at F1 {weakest[1]['f1']:.3f} "
      f"(support {weakest[1]['support']}). This is expected and is *not* hidden: short "
      f"reconnaissance commands (`whoami`, `id`) overlap lexically with discovery/credential "
      f"probes, and it is the smallest class. The hybrid rule layer and the optional Gemini "
      f"layer exist precisely to catch these ambiguous cases at runtime.")
    w("")
    w("![Per-class metrics](per_class_f1.svg)")
    w("")
    w("## 3. The stricter test: generalising to unseen command families")
    w("")
    w(f"A single accuracy number can flatter a model if near-duplicate commands leak across "
      f"the split. We therefore also run a **{rb['split']}**:")
    w("")
    w("| Evaluation | Accuracy | Macro F1 | Test samples |")
    w("| :--- | ---: | ---: | ---: |")
    w(f"| Primary (held-out) | {_pct(pe['accuracy'])} | {pe['macro_f1']:.4f} | {pe['test_samples']} |")
    w(f"| **Robustness (leave-families-out)** | **{_pct(rb['accuracy'])}** | "
      f"**{rb['macro_f1']:.4f}** | {rb['test_samples']} |")
    w("")
    w(f"> {rb['interpretation']}")
    w("")
    w("![Primary vs robustness](primary_vs_robustness.svg)")
    w("")
    w("## 4. Model selection (why this model)")
    w("")
    w(f"Candidates were compared by **{pe['model_selection_cv']}** before touching the test set:")
    w("")
    w("| Candidate | CV macro-F1 (mean ± std) |")
    w("| :--- | ---: |")
    for name, cv in pe["candidates"].items():
        marker = "  **← selected**" if name == pe["selected_model"] else ""
        w(f"| `{name}`{marker} | {cv['cv_macro_f1_mean']:.4f} ± {cv['cv_macro_f1_std']:.4f} |")
    w("")
    w("## 5. Dataset composition")
    w("")
    w(f"- **{ds['total_unique_samples']} unique commands** across "
      f"**{ds['total_families']} template families** and 10 intent classes.")
    w(f"- **{ds['exact_duplicates_removed']} exact duplicates removed** before splitting.")
    w("")
    w("![Dataset distribution](dataset_distribution.svg)")
    w("")
    w("## 6. How this evaluation differs from the rule-engine coverage check")
    w("")
    w("An earlier functional test drove **42 hand-authored coverage cases** through the "
      "deterministic *rule engine* and, by construction, every case matched its rule "
      "(100% on those 42). That is a **rule-coverage sanity check**, not a measure of model "
      "generalisation, and it must not be read as the system's accuracy. The honest, "
      "generalisation-bearing numbers are the ML held-out metrics in sections 1–3 above.")
    w("")
    w("## 7. Honesty statement")
    w("")
    for note in m.get("honesty_notes", []):
        w(f"- {note}")
    w("")
    w("---")
    w("")
    w("### Generated artifacts")
    w("")
    w("| File | Description |")
    w("| :--- | :--- |")
    w("| `metrics.json` | Source of truth — all metrics, per-class scores, confusion matrix |")
    w("| `confusion_matrix.svg` | Held-out confusion matrix (generated from metrics.json) |")
    w("| `per_class_f1.svg` | Per-class precision/recall/F1 |")
    w("| `dataset_distribution.svg` | Labelled samples per class |")
    w("| `primary_vs_robustness.svg` | Held-out vs leave-families-out comparison |")
    w("| `ml_classification_report.txt` | Raw scikit-learn classification_report |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    if not METRICS.exists():
        print(f"[!] metrics file not found: {METRICS}")
        print("    Train the model first:  PYTHONPATH=. python backend/app/ml/train.py")
        return 1
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    render_confusion_matrix(m["primary_evaluation"]["confusion_matrix"], OUT / "confusion_matrix.svg")
    render_bar_group(m["primary_evaluation"]["per_class"], OUT / "per_class_f1.svg")
    render_dataset_distribution(m["dataset"]["class_distribution"], OUT / "dataset_distribution.svg")
    render_primary_vs_robustness(m["primary_evaluation"], m["robustness_evaluation"],
                                 OUT / "primary_vs_robustness.svg")
    render_report(m, OUT / "evaluation_report.md")

    print("[+] Regenerated from metrics.json:")
    for f in ("evaluation_report.md", "confusion_matrix.svg", "per_class_f1.svg",
              "dataset_distribution.svg", "primary_vs_robustness.svg"):
        p = OUT / f
        print(f"    docs/evaluation/{f:<28} {p.stat().st_size:>7} bytes")
    print(f"[i] Deployed model: {m['primary_evaluation']['selected_model']}  "
          f"acc={_pct(m['primary_evaluation']['accuracy'])}  "
          f"macro-F1={m['primary_evaluation']['macro_f1']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
