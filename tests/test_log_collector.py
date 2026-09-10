"""
Unit and integration tests for AsyncLogCollector service.
"""

import asyncio
import os
import tempfile
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.services.log_collector import AsyncLogCollector
from backend.app.services.session_aggregator import SessionAggregator


@pytest.mark.asyncio
async def test_log_collector_reads_historical_events():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write('{"session":"sess_test_1","eventid":"cowrie.session.connect","src_ip":"127.0.0.1","timestamp":"2026-08-19T16:42:08.926448Z"}\n')
        tmp.write('{"session":"sess_test_1","eventid":"cowrie.command.input","input":"ls","timestamp":"2026-08-19T16:42:09.926448Z"}\n')
        tmp_path = tmp.name

    try:
        events_received = []

        def callback(event, session):
            events_received.append(event)

        aggregator = SessionAggregator()
        collector = AsyncLogCollector(
            log_path=tmp_path,
            aggregator=aggregator,
            from_beginning=True,
            poll_interval=0.05
        )
        collector.register_callback(callback)

        task = asyncio.create_task(collector.start())
        await asyncio.sleep(0.2)
        collector.stop()
        await task

        assert len(events_received) == 2
        assert events_received[0].event_type == "session_connect"
        assert events_received[1].event_type == "command_input"
        assert events_received[1].command == "ls"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_log_collector_incremental_live_tailing():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        # Pre-existing event
        tmp.write('{"session":"sess_old","eventid":"cowrie.session.connect","timestamp":"2026-08-19T16:00:00.000000Z"}\n')
        tmp.flush()
        tmp_path = tmp.name

    try:
        events_received = []

        def callback(event, session):
            events_received.append(event)

        aggregator = SessionAggregator()
        # Live mode (from_beginning=False) should ignore pre-existing event
        collector = AsyncLogCollector(
            log_path=tmp_path,
            aggregator=aggregator,
            from_beginning=False,
            poll_interval=0.05
        )
        collector.register_callback(callback)

        task = asyncio.create_task(collector.start())
        await asyncio.sleep(0.1)

        # Append new live event
        with open(tmp_path, "a", encoding="utf-8") as f:
            f.write('{"session":"sess_live","eventid":"cowrie.command.input","input":"whoami","timestamp":"2026-08-19T16:42:10.000000Z"}\n')
            f.flush()

        await asyncio.sleep(0.2)
        collector.stop()
        await task

        # Only the live event should have been emitted
        assert len(events_received) == 1
        assert events_received[0].session_id == "sess_live"
        assert events_received[0].command == "whoami"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_log_collector_handles_incomplete_line_buffering():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp_path = tmp.name

    try:
        events_received = []

        def callback(event, session):
            events_received.append(event)

        aggregator = SessionAggregator()
        collector = AsyncLogCollector(
            log_path=tmp_path,
            aggregator=aggregator,
            from_beginning=True,
            poll_interval=0.05
        )
        collector.register_callback(callback)

        task = asyncio.create_task(collector.start())
        await asyncio.sleep(0.1)

        # Write partial chunk (no trailing newline)
        with open(tmp_path, "a", encoding="utf-8") as f:
            f.write('{"session":"sess_chunk","eventid":"cowrie.command.input"')
            f.flush()

        await asyncio.sleep(0.1)
        assert len(events_received) == 0  # Not emitted yet because line is incomplete

        # Write remainder with newline
        with open(tmp_path, "a", encoding="utf-8") as f:
            f.write(',"input":"id","timestamp":"2026-08-19T16:42:11.000000Z"}\n')
            f.flush()

        await asyncio.sleep(0.2)
        collector.stop()
        await task

        assert len(events_received) == 1
        assert events_received[0].command == "id"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_log_collector_malformed_json_resilience():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write('MALFORMED NOT JSON LINE\n')
        tmp.write('{"session":"sess_ok","eventid":"cowrie.command.input","input":"uptime","timestamp":"2026-08-19T16:42:12.000000Z"}\n')
        tmp.write('{"session":"sess_ok", BROKEN JSON\n')
        tmp_path = tmp.name

    try:
        events_received = []

        def callback(event, session):
            events_received.append(event)

        collector = AsyncLogCollector(
            log_path=tmp_path,
            from_beginning=True,
            poll_interval=0.05
        )
        collector.register_callback(callback)

        task = asyncio.create_task(collector.start())
        await asyncio.sleep(0.2)
        collector.stop()
        await task

        # Successfully parsed valid line and did not crash on malformed lines
        assert len(events_received) == 1
        assert events_received[0].command == "uptime"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
