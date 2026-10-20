"""
Routers package for FastAPI REST API.
"""

from backend.app.api.routers.ai_security import router as ai_security_router
from backend.app.api.routers.alerts import router as alerts_router
from backend.app.api.routers.analytics import router as analytics_router
from backend.app.api.routers.attackers import router as attackers_router
from backend.app.api.routers.dashboard import router as dashboard_router
from backend.app.api.routers.deception import router as deception_router
from backend.app.api.routers.events import router as events_router
from backend.app.api.routers.financial import router as financial_router
from backend.app.api.routers.health import router as health_router
from backend.app.api.routers.research import router as research_router
from backend.app.api.routers.sessions import router as sessions_router

__all__ = [
    "health_router",
    "dashboard_router",
    "events_router",
    "sessions_router",
    "attackers_router",
    "alerts_router",
    "analytics_router",
    "deception_router",
    "research_router",
    "financial_router",
    "ai_security_router",
]
