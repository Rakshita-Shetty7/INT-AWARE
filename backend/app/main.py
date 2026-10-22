"""
FastAPI Main Application Entrypoint.
Provides REST APIs and WebSocket streams for dashboard metrics, events, sessions, attacker profiling, alerts, and analytics.
"""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
import sys
import threading
import types
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

# Self-resolving package anchor:
# Ensures 'backend' and 'backend.app' exist in sys.modules and sys.path
# regardless of whether the execution root is the repo root, backend/, or a serverless runtime (/var/task).
_CURRENT_FILE = Path(__file__).resolve()
_APP_DIR = _CURRENT_FILE.parent
_BACKEND_DIR = _APP_DIR.parent
_ROOT_DIR = _BACKEND_DIR.parent

for _p in [str(_ROOT_DIR), str(_BACKEND_DIR), str(_APP_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if "backend" not in sys.modules:
    _backend_pkg = types.ModuleType("backend")
    _backend_pkg.__path__ = [str(_BACKEND_DIR)]
    _backend_pkg.__file__ = str(_BACKEND_DIR / "__init__.py")
    sys.modules["backend"] = _backend_pkg

if "backend.app" not in sys.modules:
    if "app" in sys.modules:
        sys.modules["backend.app"] = sys.modules["app"]
    else:
        try:
            import app
            sys.modules["backend.app"] = app
        except ImportError:
            pass

from backend.app.api.routers import (
    ai_security_router,
    alerts_router,
    analytics_router,
    attackers_router,
    dashboard_router,
    deception_router,
    events_router,
    financial_router,
    health_router,
    research_router,
    sessions_router,
)
from backend.app.api.routers.websocket import router as websocket_router
from backend.app.config import settings
from backend.app.database.mongodb import mongodb_manager
from backend.app.services.websocket_manager import websocket_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend.app.main")

# Holds the background ingestion pipeline + worker thread when enabled.
_pipeline = None
_pipeline_thread = None


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes", "on")


def _run_pipeline_worker(from_beginning: bool, enable_gemini: bool) -> None:
    """
    Runs the DeceptionPipeline on a dedicated event loop in a background thread.

    The pipeline uses synchronous MongoDB (pymongo) and blocking file tailing, so
    it MUST live on its own loop/thread — never on the Uvicorn request loop.
    Cross-thread WebSocket broadcasts are marshalled back onto the main loop via
    websocket_manager (which was given the main loop in the lifespan startup).
    """
    global _pipeline
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from backend.app.pipeline import DeceptionPipeline
        _pipeline = DeceptionPipeline(from_beginning=from_beginning, enable_gemini=enable_gemini)
        loop.run_until_complete(_pipeline.start())
    except Exception as e:  # never let the worker crash the process
        logger.error("Ingestion pipeline worker terminated: %s", e, exc_info=True)
    finally:
        loop.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle.
    """
    logger.info("Initializing Intent-Aware Deception System API...")
    try:
        mongodb_manager.connect()
    except Exception as e:
        logger.warning("MongoDB connection could not be established at startup: %s", e)

    # Register main event loop with websocket manager for thread-safe cross-thread broadcasting
    websocket_manager.set_event_loop(asyncio.get_running_loop())

    # Optionally start the real-time ingestion pipeline (Cowrie log tail -> classify -> persist -> broadcast).
    # Disabled by default so the test suite / read-only API runs never start a tail thread;
    # enabled in the containerized deployment via PIPELINE_ENABLED=true.
    global _pipeline_thread
    if _env_flag("PIPELINE_ENABLED"):
        enable_gemini = settings.GEMINI_ENABLED
        from_beginning = _env_flag("PIPELINE_FROM_BEGINNING")
        _pipeline_thread = threading.Thread(
            target=_run_pipeline_worker,
            args=(from_beginning, enable_gemini),
            daemon=True,
        )
        _pipeline_thread.start()
        logger.info(
            "Background ingestion pipeline started (log_path=%s, from_beginning=%s, gemini=%s)",
            settings.COWRIE_LOG_PATH, from_beginning, enable_gemini,
        )
    else:
        logger.info("Ingestion pipeline disabled (set PIPELINE_ENABLED=true to enable).")

    yield

    logger.info("Shutting down API server...")
    if _pipeline is not None:
        try:
            _pipeline.stop()
        except Exception as e:
            logger.debug("Error stopping pipeline: %s", e)
    mongodb_manager.close()


app = FastAPI(
    title="Intent-Aware Deception System API",
    description="Real-Time Attacker Profiling and Intent Classification REST & WebSocket API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS Middleware (Restricted to configured frontend origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

# Register REST API Routers under /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(attackers_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(deception_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(financial_router, prefix="/api")
app.include_router(ai_security_router, prefix="/api")

# Register WebSocket Routers
app.include_router(websocket_router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Intent-Aware Deception System API is running",
        "docs": "/docs",
        "health": "/api/health",
        "ws_events": "/ws/events",
        "ws_alerts": "/ws/alerts"
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

