"""
Alerts REST router.
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_persistence_service
from backend.app.models.api import PaginatedResponse
from backend.app.models.database import AlertDoc
from backend.app.services.persistence_service import PersistenceService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=PaginatedResponse[AlertDoc], summary="List High-Severity Alerts")
def list_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, RESOLVED)"),
    severity: Optional[str] = Query(None, description="Filter by severity (HIGH, CRITICAL)"),
    session_id: Optional[str] = Query(None, description="Filter by Session ID"),
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves a paginated list of high-severity security alerts triggered by the risk engine.
    """
    filters = {}
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity
    if session_id:
        filters["session_id"] = session_id

    skip = (page - 1) * limit
    items, total = persistence.get_alerts(skip=skip, limit=limit, filters=filters)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return PaginatedResponse[AlertDoc](
        items=[AlertDoc(**i) for i in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )
