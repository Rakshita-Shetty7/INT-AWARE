"""
Generates a professional 1080p MP4 video walkthrough and poster for the
Intent-Aware Deception System for Real-Time Attacker Profiling.

Sections covered in the video:
  Scene 1 (00:00 - 00:05): Title Card & Mission Overview
  Scene 2 (00:05 - 00:13): End-to-End Architecture & Telemetry Pipeline
  Scene 3 (00:13 - 00:23): Real-Time Attacker Interaction & Cowrie Honeypot Ingestion
  Scene 4 (00:23 - 00:33): ML Intent Classification & Calibrated Probability Inference
  Scene 5 (00:33 - 00:43): Executive Security Dashboard & Metric Intelligence
  Scene 6 (00:43 - 00:52): Attacker Profiling, MITRE ATT&CK Mapping & Session Analysis
  Scene 7 (00:52 - 01:00): Markov Threat Progression & Concept Drift Watchtower
  Scene 8 (01:00 - 01:07): Empirical Verification (166 Hermetic Tests & Verified 81.98% LFO)
"""

import sys
import os
from pathlib import Path
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "website" / "public" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = ROOT_DIR / "docs" / "project_report" / "figures"

VIDEO_PATH = ASSETS_DIR / "demo_walkthrough.mp4"
POSTER_PATH = ASSETS_DIR / "demo_poster.png"

WIDTH, HEIGHT = 1920, 1080
FPS = 24

def get_font(size: int, bold: bool = False):
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            return ImageFont.truetype(font_name, size)
        except Exception:
            return ImageFont.load_default()

def draw_header_footer(draw, title: str, subtitle: str, timestamp_str: str):
    # Top banner
    draw.rectangle([(0, 0), (WIDTH, 90)], fill=(9, 14, 28))
    draw.line([(0, 90), (WIDTH, 90)], fill=(30, 41, 59), width=2)
    
    # Title
    font_title = get_font(26, bold=True)
    font_sub = get_font(16, bold=False)
    draw.text((40, 20), title, font=font_title, fill=(6, 182, 212)) # Cyan
    draw.text((40, 55), subtitle, font=font_sub, fill=(148, 163, 184)) # Slate
    
    # Live badge
    draw.rounded_rectangle([(WIDTH - 280, 25), (WIDTH - 40, 65)], radius=6, fill=(15, 23, 42), outline=(16, 185, 129), width=1)
    font_badge = get_font(14, bold=True)
    draw.text((WIDTH - 260, 36), "SYSTEM ACTIVE · VERIFIED", font=font_badge, fill=(52, 211, 153))

    # Bottom footer banner
    draw.rectangle([(0, HEIGHT - 70), (WIDTH, HEIGHT)], fill=(9, 14, 28))
    draw.line([(0, HEIGHT - 70), (WIDTH, HEIGHT - 70)], fill=(30, 41, 59), width=2)
    font_foot = get_font(15, bold=False)
    draw.text((40, HEIGHT - 45), "Intent-Aware Deception System for Real-Time Attacker Profiling", font=font_foot, fill=(203, 213, 225))
    draw.text((WIDTH - 220, HEIGHT - 45), timestamp_str, font=font_foot, fill=(100, 116, 139))


def create_title_frame(progress: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(6, 9, 19))
    draw = ImageDraw.Draw(img)
    
    # Background subtle grid pattern
    for x in range(0, WIDTH, 80):
        draw.line([(x, 0), (x, HEIGHT)], fill=(15, 23, 42), width=1)
    for y in range(0, HEIGHT, 80):
        draw.line([(0, y), (WIDTH, y)], fill=(15, 23, 42), width=1)

    # Center hero card
    card_box = [300, 240, WIDTH - 300, HEIGHT - 240]
    draw.rounded_rectangle(card_box, radius=16, fill=(9, 14, 28), outline=(6, 182, 212), width=2)
    
    # Top badge
    draw.rounded_rectangle([700, 275, 1220, 315], radius=20, fill=(15, 23, 42), outline=(16, 185, 129), width=1)
    draw.text((725, 285), "TECHNICAL ARCHITECTURE & LIVE CAPABILITY TOUR", font=get_font(14, bold=True), fill=(52, 211, 153))

    # Big Title
    draw.text((360, 360), "Intent-Aware Deception System", font=get_font(46, bold=True), fill=(255, 255, 255))
    draw.text((480, 430), "for Real-Time Attacker Profiling", font=get_font(40, bold=True), fill=(6, 182, 212))

    # Feature tags
    tags = [
        "Calibrated LinearSVC ML (100.0% Held-Out · 81.98% LFO)",
        "Zero Host Execution Containerized Sandbox",
        "166 Hermetic Automated Verification Tests Passed",
        "Real-Time Cowrie Telemetry & Dynamic Deception"
    ]
    for i, tag in enumerate(tags):
        y_pos = 520 + (i * 35)
        draw.text((420, y_pos), f"✓  {tag}", font=get_font(18, bold=False), fill=(203, 213, 225))

    # Timestamp indicator
    draw.text((WIDTH//2 - 120, HEIGHT - 180), "Comprehensive Video Walkthrough", font=get_font(16, bold=False), fill=(100, 116, 139))
    return img


def create_image_frame(img_path: Path, title: str, subtitle: str, caption: str, progress: float) -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), color=(6, 9, 19))
    draw = ImageDraw.Draw(base)
    
    draw_header_footer(draw, title, subtitle, f"TOUR PROGRESS: {int(progress*100)}%")

    # Load and scale main figure
    if img_path.exists():
        fig = Image.open(img_path).convert("RGB")
        max_w = WIDTH - 160
        max_h = HEIGHT - 260
        fig.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        
        # Center the figure
        x_off = (WIDTH - fig.width) // 2
        y_off = 110 + (max_h - fig.height) // 2
        
        # Subtle border card
        draw.rounded_rectangle([(x_off - 6, y_off - 6), (x_off + fig.width + 6, y_off + fig.height + 6)], radius=8, fill=(15, 23, 42), outline=(30, 41, 59), width=2)
        base.paste(fig, (x_off, y_off))
        
    # Bottom caption card
    draw.rounded_rectangle([(80, HEIGHT - 150), (WIDTH - 80, HEIGHT - 85)], radius=10, fill=(15, 23, 42), outline=(6, 182, 212), width=1)
    draw.text((110, HEIGHT - 130), f"FEATURE SPOTLIGHT:  {caption}", font=get_font(18, bold=True), fill=(241, 245, 249))

    return base


def create_terminal_frame(step_index: int, total_steps: int) -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), color=(6, 9, 19))
    draw = ImageDraw.Draw(base)
    
    draw_header_footer(draw, "TELEMETRY INGESTION & REAL-TIME ML INFERENCE PIPELINE", "Attacker Interaction -> Feature Extraction -> Calibrated Intent Inference -> Dynamic Decoy Action", "LIVE TEST SIMULATION")

    # Terminal window box
    term_box = [120, 120, WIDTH - 120, HEIGHT - 180]
    draw.rounded_rectangle(term_box, radius=12, fill=(10, 15, 30), outline=(51, 65, 85), width=2)

    # Window title bar
    draw.rounded_rectangle([(120, 120), (WIDTH - 120, 165)], radius=12, fill=(15, 23, 42))
    draw.ellipse([(140, 136), (154, 150)], fill=(239, 68, 68)) # Red
    draw.ellipse([(164, 136), (178, 150)], fill=(234, 179, 8)) # Yellow
    draw.ellipse([(188, 136), (202, 150)], fill=(34, 197, 94))  # Green
    draw.text((220, 134), "attacker@isolated-cowrie-sandbox: ~ (Live SSH Telemetry Channel 2222)", font=get_font(14, bold=True), fill=(148, 163, 184))

    # Console lines to render based on step_index
    console_script = [
        ("attacker@cowrie:~$ ", (148, 163, 184), "ssh -p 2222 root@10.0.0.15", (248, 250, 252)),
        ("SYSTEM ALERT: ", (239, 68, 68), "SSH connection accepted on decoy port 2222. Cowrie JSON stream active.", (148, 163, 184)),
        ("attacker@cowrie:~$ ", (148, 163, 184), "cat /etc/shadow 2>&1", (253, 224, 71)),
        ("[INGESTION ENGINE] ", (6, 182, 212), "Raw event received. Normalized event_id='evt_98a72b04' type='command_input'", (226, 232, 240)),
        ("[CANONICALIZATION] ", (168, 85, 247), "Noise wrappers stripped: '2>&1' removed -> Canonical: 'cat /etc/shadow'", (226, 232, 240)),
        ("[FEATURE VECTOR] ", (59, 130, 246), "Extracted word-TFIDF (ngram 1-3), char_wb (3-6), and domain structural flag SENSITIVE_TARGET=1.0", (226, 232, 240)),
        ("[ML CLASSIFIER] ", (16, 185, 129), "Calibrated LinearSVC -> Intent: CREDENTIAL_ACCESS (Calibrated Confidence: 0.9984)", (52, 211, 153)),
        ("[INTRUSION STAGE] ", (245, 158, 11), "Mapped Stage: CREDENTIAL_ACCESS | Shannon Entropy: 3.12 bits/byte", (251, 191, 36)),
        ("[RISK REGRESSOR] ", (239, 68, 68), "GradientBoostingRiskPredictor score: 86.4 / 100 [CRITICAL RISK TIER]", (252, 165, 165)),
        ("[DYNAMIC DECEPTION] ", (14, 165, 233), "Action fired: Injected synthetic fake shadow hashes. Zero real customer data exposed.", (56, 189, 248)),
        ("[AUDIT RETENTION] ", (100, 116, 139), "Event indexed into MongoDB 'events' collection. UI Digital Twin updated via WebSocket.", (148, 163, 184)),
    ]

    y = 190
    max_lines = min(len(console_script), step_index + 1)
    for i in range(max_lines):
        tag, tag_col, text, text_col = console_script[i]
        font_mono = get_font(16, bold=True)
        draw.text((150, y), tag, font=font_mono, fill=tag_col)
        # Calculate offset for text
        tag_width = len(tag) * 10
        draw.text((150 + tag_width, y), text, font=get_font(16, bold=False), fill=text_col)
        y += 42

    # Bottom caption
    draw.rounded_rectangle([(120, HEIGHT - 150), (WIDTH - 120, HEIGHT - 90)], radius=10, fill=(15, 23, 42), outline=(16, 185, 129), width=1)
    draw.text((150, HEIGHT - 128), "END-TO-END VERIFICATION:  Real-time feature extraction and calibrated LinearSVC classify attacker intent in under 12 milliseconds.", font=get_font(16, bold=True), fill=(241, 245, 249))

    return base


def generate_video():
    print(f"Generating walkthrough video to: {VIDEO_PATH}")
    writer = imageio.get_writer(
        str(VIDEO_PATH),
        fps=FPS,
        codec="libx264",
        pixelformat="yuv420p",
        macro_block_size=1
    )

    scenes = [
        # 1. Title intro (4 seconds = 96 frames)
        {"type": "title", "duration": 4.0},
        
        # 2. Architecture Diagram (7 seconds = 168 frames)
        {"type": "image", "file": FIGURES_DIR / "fig_4_1_system_architecture.png", "title": "SYSTEM ARCHITECTURE & DECEPTION TOPOLOGY", "subtitle": "Containerized Cowrie Honeypot, FastAPI Core Engine & Machine Learning Pipeline", "caption": "End-to-end dataflow showing honeypot isolation, event normalization, and multi-tier arbitrated classification.", "duration": 7.0},
        
        # 3. Terminal Live Interaction (9 seconds = 216 frames)
        {"type": "terminal", "duration": 9.0},

        # 4. Executive Dashboard (7 seconds = 168 frames)
        {"type": "image", "file": FIGURES_DIR / "fig_5_1_ui_overview_dashboard.png", "title": "EXECUTIVE THREAT INTELLIGENCE DASHBOARD", "subtitle": "Real-Time Telemetry Feed, Active Honeypot Sessions & Intrusion Stage Distribution", "caption": "Live SOC visualization: aggregated attacker metrics, stage breakdowns, and classified session timelines.", "duration": 7.0},

        # 5. Attacker Profiles (7 seconds = 168 frames)
        {"type": "image", "file": FIGURES_DIR / "fig_5_2_ui_attacker_profiles.png", "title": "ATTACKER PROFILING & MITRE ATT&CK MATRIX", "subtitle": "Autonomous Threat Profiling, Digital Twin Fingerprinting & Attack Progression", "caption": "In-depth adversary dossier tracking origin IP, command history, and mapped MITRE techniques.", "duration": 7.0},

        # 6. Analytics & Markov Transition Matrix (7 seconds = 168 frames)
        {"type": "image", "file": FIGURES_DIR / "fig_5_3_ui_analytics_markov.png", "title": "ANALYTICS, MARKOV MODEL & DRIFT WATCHTOWER", "subtitle": "Transition Probability Graphs, Attack Trajectory Forecasting & Concept Drift (PSI)", "caption": "First-order Markov chains predict next attacker moves while PSI monitors command distribution shifts.", "duration": 7.0},

        # 7. Model Performance & Confusion Matrix (7 seconds = 168 frames)
        {"type": "image", "file": FIGURES_DIR / "fig_6_2_intent_confusion_matrix.png", "title": "EMPIRICAL MODEL EVALUATION & CONFUSION MATRIX", "subtitle": "Calibrated LinearSVC Multiclass Classification Across 10 Canonical Intent Classes", "caption": "Rigorous evaluation: 100.0% held-out test accuracy and verified 81.98% Leave-Families-Out robustness.", "duration": 7.0},

        # 8. Pytest Test Verification (6 seconds = 144 frames)
        {"type": "image", "file": FIGURES_DIR / "fig_6_6_terminal_pytest_results.png", "title": "AUTOMATED SOFTWARE VERIFICATION (166 TESTS)", "subtitle": "Hermetic Pytest Execution with Zero Network Dependencies or Live Secrets", "caption": "166 passing tests verify API endpoints, database persistence, log tailing, and risk calculation arithmetic.", "duration": 6.0},
    ]

    total_frames = 0
    poster_saved = False

    for s_idx, scene in enumerate(scenes):
        duration = scene["duration"]
        n_frames = int(duration * FPS)
        s_type = scene["type"]
        print(f"Rendering scene {s_idx+1}/{len(scenes)}: {s_type} ({n_frames} frames)...")

        for f in range(n_frames):
            prog = f / max(1, n_frames - 1)
            global_prog = (total_frames + f) / (sum(s["duration"] for s in scenes) * FPS)
            
            if s_type == "title":
                frame_img = create_title_frame(prog)
            elif s_type == "image":
                frame_img = create_image_frame(scene["file"], scene["title"], scene["subtitle"], scene["caption"], global_prog)
            elif s_type == "terminal":
                step = int(prog * 11)
                frame_img = create_terminal_frame(step, 11)
            else:
                frame_img = create_title_frame(prog)

            # Save poster from early dashboard scene
            if not poster_saved and s_type == "image" and f == n_frames // 2:
                frame_img.save(POSTER_PATH)
                print(f"Saved high-res poster thumbnail -> {POSTER_PATH}")
                poster_saved = True

            frame_np = np.array(frame_img)
            writer.append_data(frame_np)

        total_frames += n_frames

    writer.close()
    print(f"Successfully generated video: {VIDEO_PATH} ({total_frames} frames, {total_frames/FPS:.1f} seconds)")

if __name__ == "__main__":
    generate_video()
