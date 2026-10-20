"""
WebSocket Streaming Router for Live Events and Security Alerts.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket channel streaming newly ingested and analyzed honeypot events in real time.
    """
    await websocket_manager.connect_events(websocket)
    try:
        while True:
            # Keep connection open and receive potential client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await websocket_manager.disconnect_events(websocket)
    except Exception as e:
        logger.debug("[WS] /ws/events connection closed: %s", e)
        await websocket_manager.disconnect_events(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    WebSocket channel streaming high-severity and critical security alerts in real time.
    """
    await websocket_manager.connect_alerts(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await websocket_manager.disconnect_alerts(websocket)
    except Exception as e:
        logger.debug("[WS] /ws/alerts connection closed: %s", e)
        await websocket_manager.disconnect_alerts(websocket)
