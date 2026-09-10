"""
Attackers REST router.
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.dependencies import get_persistence_service
from backend.app.models.api import PaginatedResponse
from backend.app.models.database import AttackerProfileDoc
from backend.app.services.persistence_service import PersistenceService

router = APIRouter(prefix="/attackers", tags=["Attackers"])


@router.get("", response_model=PaginatedResponse[AttackerProfileDoc], summary="List Attacker Profiles")
def list_attackers(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    source_ip: Optional[str] = Query(None, description="Search by exact IP"),
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves a paginated list of distinct attacker host profiles ordered by maximum threat risk.
    """
    filters = {}
    if source_ip:
        filters["source_ip"] = source_ip

    skip = (page - 1) * limit
    items, total = persistence.get_attackers(skip=skip, limit=limit, filters=filters)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return PaginatedResponse[AttackerProfileDoc](
        items=[AttackerProfileDoc(**i) for i in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/{source_ip}", response_model=AttackerProfileDoc, summary="Get Attacker Profile by IP")
def get_attacker(
    source_ip: str,
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves aggregated threat intelligence, session history, and peak risk score for a specific source IP.
    """
    attacker = persistence.get_attacker(source_ip)
    if not attacker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attacker profile for IP '{source_ip}' not found"
        )
    return AttackerProfileDoc(**attacker)
