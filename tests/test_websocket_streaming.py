"""
Unit and integration tests for real-time WebSocket streaming endpoints (/ws/events, /ws/alerts).
"""

import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.services.websocket_manager import websocket_manager


def test_websocket_ping_pong():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/events") as websocket:
            websocket.send_text("ping")
            response = websocket.receive_text()
            assert response == "pong"


def test_websocket_events_broadcast():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/events") as ws:
            # Broadcast event payload
            event_payload = {
                "type": "event",
                "event_id": "ev_ws_test_01",
                "session_id": "sess_ws_01",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": "10.0.0.99",
                "command": "cat /etc/passwd",
                "intent": "DISCOVERY",
                "attack_stage": "DISCOVERY",
                "confidence": 0.90,
                "classification_source": "RULE",
                "risk_score": 25,
                "severity": "MEDIUM"
            }
            asyncio.run(websocket_manager.broadcast_event_async(event_payload))

            received = ws.receive_json()
            assert received["type"] == "event"
            assert received["event_id"] == "ev_ws_test_01"
            assert received["intent"] == "DISCOVERY"
            assert received["risk_score"] == 25
            assert "password" not in received


def test_websocket_alerts_broadcast():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/alerts") as ws:
            alert_payload = {
                "type": "alert",
                "alert_id": "ALT-TEST001",
                "session_id": "sess_crit_99",
                "source_ip": "10.0.0.99",
                "intent": "EXFILTRATION",
                "attack_stage": "EXFILTRATION",
                "risk_score": 85,
                "severity": "CRITICAL",
                "reason": "Exfiltration attempt detected",
                "status": "OPEN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            asyncio.run(websocket_manager.broadcast_alert_async(alert_payload))

            received = ws.receive_json()
            assert received["type"] == "alert"
            assert received["alert_id"] == "ALT-TEST001"
            assert received["severity"] == "CRITICAL"
            assert received["risk_score"] == 85


def test_websocket_multiple_subscribers():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/events") as ws1:
            with client.websocket_connect("/ws/events") as ws2:
                payload = {
                    "type": "event",
                    "event_id": "ev_multi_sub",
                    "session_id": "s_multi",
                    "intent": "RECONNAISSANCE",
                    "risk_score": 10
                }
                asyncio.run(websocket_manager.broadcast_event_async(payload))

                res1 = ws1.receive_json()
                res2 = ws2.receive_json()
                assert res1["event_id"] == "ev_multi_sub"
                assert res2["event_id"] == "ev_multi_sub"
