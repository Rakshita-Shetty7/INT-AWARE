"""
Dashboard statistics router.
"""

from fastapi import APIRouter, Depends
from backend.app.api.dependencies import get_persistence_service
from backend.app.models.api import DashboardStatsResponse
from backend.app.services.persistence_service import PersistenceService

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse, summary="Executive Dashboard Statistics")
def get_dashboard_stats(
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns aggregated metrics and risk indicators for the deception dashboard.
    """
    stats = persistence.get_dashboard_stats()
    return DashboardStatsResponse(**stats)
