"""
Events REST router.
"""

from datetime import datetime
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.dependencies import get_persistence_service
from backend.app.models.api import PaginatedResponse
from backend.app.models.database import StoredEventDoc
from backend.app.services.persistence_service import PersistenceService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=PaginatedResponse[StoredEventDoc], summary="List Analyzed Events")
def list_events(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    session_id: Optional[str] = Query(None, description="Filter by Session ID"),
    source_ip: Optional[str] = Query(None, description="Filter by Attacker IP"),
    intent: Optional[str] = Query(None, description="Filter by Intent Category"),
    severity: Optional[str] = Query(None, description="Filter by Risk Severity"),
    start_time: Optional[datetime] = Query(None, description="Filter events after timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter events before timestamp"),
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves a paginated list of analyzed honeypot events with optional security filters.
    """
    filters = {}
    if session_id:
        filters["session_id"] = session_id
    if source_ip:
        filters["source_ip"] = source_ip
    if intent:
        filters["intent"] = intent
    if severity:
        filters["severity"] = severity
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time

    skip = (page - 1) * limit
    items, total = persistence.get_events(skip=skip, limit=limit, filters=filters)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return PaginatedResponse[StoredEventDoc](
        items=[StoredEventDoc(**i) for i in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/recent", response_model=List[StoredEventDoc], summary="Get Recent Events Stream")
def get_recent_events(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recent events"),
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns the most recent events for live dashboard monitoring.
    """
    items = persistence.get_recent_events(limit=limit)
    return [StoredEventDoc(**i) for i in items]


@router.get("/{event_id}", response_model=StoredEventDoc, summary="Get Single Event Detail")
def get_event(
    event_id: str,
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves comprehensive telemetry, AI reasoning, and risk calculation for a specific event ID.
    """
    event = persistence.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found"
        )
    return StoredEventDoc(**event)
