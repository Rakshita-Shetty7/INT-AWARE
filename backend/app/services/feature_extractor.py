"""
Feature Extraction Engine Service.
Extracts behavioral features at both event and session levels.
"""

from datetime import datetime
import shlex
from typing import List, Optional

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import EventFeatures, SessionFeatures


class FeatureExtractor:
    """
    Extracts deterministic statistical and behavioral feature vectors from NormalizedEvents.
    """

    @staticmethod
    def extract_event_features(event: NormalizedEvent) -> EventFeatures:
        """
        Extracts granular behavioral features from a single event.
        """
        has_command = event.command is not None and len(event.command.strip()) > 0
        cmd_str = event.command.strip() if has_command else ""
        cmd_len = len(cmd_str)
        
        # Token count
        token_count = 0
        if has_command:
            try:
                tokens = shlex.split(cmd_str)
                token_count = len(tokens)
            except Exception:
                token_count = len(cmd_str.split())

        return EventFeatures(
            session_id=event.session_id,
            event_type=event.event_type,
            has_command=has_command,
            command=cmd_str if has_command else None,
            command_length=cmd_len,
            command_token_count=token_count,
            timestamp=event.timestamp
        )

    @classmethod
    def compute_session_features(cls, session_id: str, events: List[NormalizedEvent]) -> SessionFeatures:
        """
        Computes comprehensive behavioral features across the entire sequence of events for a session.
        """
        if not events:
            return SessionFeatures(session_id=session_id)

        # Sort events chronologically
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        first_event = sorted_events[0]
        last_event = sorted_events[-1]

        first_seen = first_event.timestamp
        last_seen = last_event.timestamp
        duration = max(0.0, (last_seen - first_seen).total_seconds())

        # Collect session metadata
        source_ip = next((e.source_ip for e in sorted_events if e.source_ip), None)
        protocol = next((e.protocol for e in sorted_events if e.protocol), None)
        username = next((e.username for e in reversed(sorted_events) if e.username), None)

        total_events = len(sorted_events)
        event_types: dict[str, int] = {}
        commands: List[str] = []
        command_timestamps: List[datetime] = []
        login_success_count = 0
        login_failed_count = 0
        is_closed = False

        for ev in sorted_events:
            # Event type histogram
            event_types[ev.event_type] = event_types.get(ev.event_type, 0) + 1

            if ev.event_type == "login_success":
                login_success_count += 1
            elif ev.event_type == "login_failed":
                login_failed_count += 1
            elif ev.event_type == "session_closed":
                is_closed = True

            if ev.command and ev.command.strip():
                commands.append(ev.command.strip())
                command_timestamps.append(ev.timestamp)

        command_count = len(commands)
        unique_commands = list(dict.fromkeys(commands))
        unique_command_count = len(unique_commands)
        login_attempt_count = login_success_count + login_failed_count

        # Command interval calculation
        command_intervals: List[float] = []
        for i in range(1, len(command_timestamps)):
            delta = max(0.0, (command_timestamps[i] - command_timestamps[i - 1]).total_seconds())
            command_intervals.append(round(delta, 3))

        avg_command_interval: Optional[float] = None
        if command_intervals:
            avg_command_interval = round(sum(command_intervals) / len(command_intervals), 3)

        # Rates (events/sec, commands/sec)
        activity_rate = 0.0
        command_frequency = 0.0
        if duration > 0:
            activity_rate = round(total_events / duration, 3)
            command_frequency = round(command_count / duration, 3)
        else:
            activity_rate = float(total_events)
            command_frequency = float(command_count)

        return SessionFeatures(
            session_id=session_id,
            source_ip=source_ip,
            protocol=protocol,
            username=username,
            first_seen=first_seen,
            last_seen=last_seen,
            duration_seconds=round(duration, 3),
            total_events=total_events,
            command_count=command_count,
            unique_commands=unique_commands,
            unique_command_count=unique_command_count,
            login_attempt_count=login_attempt_count,
            login_success_count=login_success_count,
            login_failed_count=login_failed_count,
            event_types=event_types,
            distinct_event_types_count=len(event_types),
            commands=commands,
            command_intervals=command_intervals,
            average_command_interval=avg_command_interval,
            activity_rate=activity_rate,
            command_frequency=command_frequency,
            is_closed=is_closed
        )
