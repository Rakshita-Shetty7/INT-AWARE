#!/usr/bin/env python3
"""
Launcher script for FastAPI REST API Server and Ingestion Pipeline.
"""

import argparse
import asyncio
import logging
import os
import sys
import threading
from pathlib import Path
import uvicorn

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.pipeline import DeceptionPipeline


def start_pipeline_worker(from_beginning: bool, no_gemini: bool):
    """
    Runs the DeceptionPipeline in a dedicated background worker thread.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    pipeline = DeceptionPipeline(
        from_beginning=from_beginning,
        enable_gemini=not no_gemini
    )

    try:
        loop.run_until_complete(pipeline.start())
    except Exception as e:
        logging.error("Pipeline worker terminated: %s", e)
    finally:
        loop.close()


def main():
    parser = argparse.ArgumentParser(description="Intent-Aware Deception System — Backend Server")
    parser.add_argument("--host", default=settings.API_HOST, help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=settings.API_PORT, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--with-pipeline", action="store_true", help="Start background log ingestion pipeline")
    parser.add_argument("--from-beginning", action="store_true", help="Replay logs from beginning on pipeline startup")
    parser.add_argument("--no-gemini", action="store_true", help="Disable Gemini LLM in pipeline")
    args = parser.parse_args()

    if args.with_pipeline:
        worker_thread = threading.Thread(
            target=start_pipeline_worker,
            args=(args.from_beginning, args.no_gemini),
            daemon=True
        )
        worker_thread.start()
        print(f"[*] Background DeceptionPipeline started (from_beginning={args.from_beginning})")

    print(f"[*] Starting FastAPI REST API on http://{args.host}:{args.port}")
    print(f"[*] Interactive Swagger Docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "backend.app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
