"""
Sessions REST router.
Provides endpoints for session listings, detail retrieval, MITRE ATT&CK mapping, and AI session analysis.
"""

import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.dependencies import get_persistence_service
from backend.app.models.api import PaginatedResponse
from backend.app.models.database import StoredSessionDoc
from backend.app.services.gemini_session_analyst import SessionAnalysisReport, gemini_session_analyst
from backend.app.services.mitre_mapper import MitreMapper
from backend.app.services.persistence_service import PersistenceService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=PaginatedResponse[StoredSessionDoc], summary="List Attacker Sessions")
def list_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    source_ip: Optional[str] = Query(None, description="Filter by Attacker IP"),
    severity: Optional[str] = Query(None, description="Filter by Session Severity"),
    intent: Optional[str] = Query(None, description="Filter by Dominant Intent"),
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves a paginated list of attacker session profiles and multi-stage lifecycle trajectories.
    """
    filters = {}
    if source_ip:
        filters["source_ip"] = source_ip
    if severity:
        filters["severity"] = severity
    if intent:
        filters["intent"] = intent

    skip = (page - 1) * limit
    items, total = persistence.get_sessions(skip=skip, limit=limit, filters=filters)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return PaginatedResponse[StoredSessionDoc](
        items=[StoredSessionDoc(**i) for i in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/{session_id}", response_model=StoredSessionDoc, summary="Get Single Session Profile")
def get_session(
    session_id: str,
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Retrieves session profile, dominant intent, attack progression, and key evidence.
    """
    session = persistence.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session profile with ID '{session_id}' not found."
        )
    return StoredSessionDoc(**session)


@router.post("/{session_id}/analyze", response_model=SessionAnalysisReport, summary="Analyze Session with AI Analyst")
def analyze_session_endpoint(
    session_id: str,
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Generates a structured cybersecurity threat assessment using Google Gemini (with deterministic fallback).
    Explains the adversary objective, progression, key indicators, threat interpretation, and defensive response.
    """
    session = persistence.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found for analysis."
        )

    # Fetch associated session events
    events, _ = persistence.get_events(limit=200, filters={"session_id": session_id})

    # Run AI Session Analysis
    report = gemini_session_analyst.analyze_session(session, events)
    return report


@router.get("/{session_id}/mitre", response_model=List[Dict[str, Any]], summary="Get MITRE ATT&CK Mapping for Session")
def get_session_mitre_mapping(
    session_id: str,
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Returns mapped MITRE ATT&CK tactics and techniques based on observed session behaviors.
    """
    session = persistence.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )

    events, _ = persistence.get_events(limit=200, filters={"session_id": session_id})
    return MitreMapper.map_session(session, events)
