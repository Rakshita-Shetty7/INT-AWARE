"""
WebSocket Connection Manager and Real-Time Event Broadcaster.
Handles client connection lifecycles, graceful disconnects, and thread-safe event/alert dispatch.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket client connections across event and alert channels.
    """

    def __init__(self):
        self._event_subscribers: Set[WebSocket] = set()
        self._alert_subscribers: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Sets the main asyncio loop for cross-thread event dispatching.
        """
        self._loop = loop

    async def connect_events(self, websocket: WebSocket) -> None:
        """
        Registers a new client on the /ws/events stream.
        """
        await websocket.accept()
        async with self._lock:
            self._event_subscribers.add(websocket)
        logger.info("[WS] New subscriber connected to /ws/events. Active subscribers: %d", len(self._event_subscribers))

    async def disconnect_events(self, websocket: WebSocket) -> None:
        """
        Unregisters a client from the /ws/events stream.
        """
        async with self._lock:
            self._event_subscribers.discard(websocket)
        logger.info("[WS] Subscriber disconnected from /ws/events. Remaining subscribers: %d", len(self._event_subscribers))

    async def connect_alerts(self, websocket: WebSocket) -> None:
        """
        Registers a new client on the /ws/alerts stream.
        """
        await websocket.accept()
        async with self._lock:
            self._alert_subscribers.add(websocket)
        logger.info("[WS] New subscriber connected to /ws/alerts. Active subscribers: %d", len(self._alert_subscribers))

    async def disconnect_alerts(self, websocket: WebSocket) -> None:
        """
        Unregisters a client from the /ws/alerts stream.
        """
        async with self._lock:
            self._alert_subscribers.discard(websocket)
        logger.info("[WS] Subscriber disconnected from /ws/alerts. Remaining subscribers: %d", len(self._alert_subscribers))

    async def _broadcast(self, subscribers: Set[WebSocket], message: Dict[str, Any]) -> None:
        """
        Internal safe broadcast implementation with stale connection pruning.
        """
        if not subscribers:
            return

        stale: List[WebSocket] = []
        # Create a shallow snapshot to avoid mutation during iteration
        async with self._lock:
            targets = list(subscribers)

        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception as err:
                logger.debug("[WS] Error sending message to client: %s", err)
                stale.append(ws)

        if stale:
            async with self._lock:
                for ws in stale:
                    subscribers.discard(ws)
            logger.debug("[WS] Pruned %d disconnected WebSocket clients", len(stale))

    async def broadcast_event_async(self, event_data: Dict[str, Any]) -> None:
        """
        Asynchronously broadcasts a sanitized event payload to /ws/events subscribers.
        """
        await self._broadcast(self._event_subscribers, event_data)

    async def broadcast_alert_async(self, alert_data: Dict[str, Any]) -> None:
        """
        Asynchronously broadcasts a security alert payload to /ws/alerts subscribers.
        """
        await self._broadcast(self._alert_subscribers, alert_data)

    def broadcast_event(self, event_data: Dict[str, Any]) -> None:
        """
        Thread-safe broadcast method that safely schedules async dispatching
        from either the main asyncio loop or background worker threads.
        """
        target_loop = self._loop
        if target_loop is not None and target_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self.broadcast_event_async(event_data), target_loop)
                return
            except Exception as e:
                logger.debug("[WS] Error scheduling broadcast to target loop: %s", e)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast_event_async(event_data), loop)
            else:
                loop.run_until_complete(self.broadcast_event_async(event_data))
        except (RuntimeError, Exception) as err:
            logger.debug("[WS] Event broadcast skipped: %s", err)

    def broadcast_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        Thread-safe broadcast method for critical alerts.
        """
        target_loop = self._loop
        if target_loop is not None and target_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self.broadcast_alert_async(alert_data), target_loop)
                return
            except Exception as e:
                logger.debug("[WS] Error scheduling alert broadcast to target loop: %s", e)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast_alert_async(alert_data), loop)
            else:
                loop.run_until_complete(self.broadcast_alert_async(alert_data))
        except (RuntimeError, Exception) as err:
            logger.debug("[WS] Alert broadcast skipped: %s", err)


# Global singleton instance
websocket_manager = ConnectionManager()
