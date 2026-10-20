"""
Asynchronous Cowrie Log Collector Service.
Monitors cowrie.json in real time, buffers incomplete lines, normalizes incoming events,
and emits them to registered callbacks and the SessionAggregator.
"""

import asyncio
import logging
import os
from pathlib import Path
from collections import OrderedDict
from typing import Any, Callable, Coroutine, List, Optional, Union

from backend.app.config import settings
from backend.app.models.events import NormalizedEvent
from backend.app.services.event_normalizer import EventNormalizer
from backend.app.services.session_aggregator import SessionAggregator

logger = logging.getLogger(__name__)

# Callback type accepting (NormalizedEvent, SessionFeatures)
EventCallback = Callable[[NormalizedEvent, Any], Union[None, Coroutine[Any, Any, None]]]


class AsyncLogCollector:
    """
    Asynchronous file tailer and event emitter for Cowrie JSON telemetry.
    """

    def __init__(
        self,
        log_path: Union[str, Path],
        aggregator: Optional[SessionAggregator] = None,
        from_beginning: bool = False,
        poll_interval: float = 0.2,
        max_processed_ids: Optional[int] = None
    ):
        self.log_path = Path(log_path).resolve()
        self.aggregator = aggregator or SessionAggregator()
        self.from_beginning = from_beginning
        self.poll_interval = poll_interval
        self._running = False
        self._stop_event = asyncio.Event()
        self._callbacks: List[EventCallback] = []
        self._max_processed_ids = max_processed_ids if max_processed_ids is not None else settings.PROCESSED_ID_CACHE_MAX
        # Bounded FIFO of seen event_ids for de-duplication (oldest evicted first).
        self._processed_event_ids: "OrderedDict[str, None]" = OrderedDict()
        self._current_offset: int = 0
        self._buffer: str = ""

    def register_callback(self, callback: EventCallback) -> None:
        """
        Registers an async or sync callback to receive normalized events and updated session features.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    async def _emit(self, event: NormalizedEvent) -> None:
        """
        Emits normalized events to the SessionAggregator and all registered listeners.
        """
        # Incrementally update session aggregator
        session_features = self.aggregator.add_event(event)

        # Notify registered callbacks
        for cb in self._callbacks:
            try:
                res = cb(event, session_features)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error("Error in event callback: %s", e, exc_info=True)

    def _process_line(self, line: str) -> Optional[NormalizedEvent]:
        """
        Parses a single raw line, normalizes it, and returns the NormalizedEvent if unique.
        """
        clean_line = line.strip()
        if not clean_line:
            return None

        event = EventNormalizer.normalize(clean_line)
        if event is None:
            return None

        # Duplicate event check
        if event.event_id in self._processed_event_ids:
            logger.debug("Skipping duplicate event_id: %s", event.event_id)
            return None

        self._processed_event_ids[event.event_id] = None
        # Enforce the FIFO cap so the de-dup cache cannot grow without bound.
        if len(self._processed_event_ids) > self._max_processed_ids:
            self._processed_event_ids.popitem(last=False)
        return event

    async def _sleep_or_stop(self) -> bool:
        """
        Sleeps for one poll interval without blocking the event loop.
        Returns True if a stop was requested during the wait, False on timeout.
        """
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_interval)
            return True
        except asyncio.TimeoutError:
            return False

    @staticmethod
    def _file_identity(stat_result) -> tuple:
        """Returns a stable (device, inode) identity used to detect log rotation."""
        return (stat_result.st_dev, stat_result.st_ino)

    async def start(self) -> None:
        """
        Starts the asynchronous, rotation-safe log tailing loop.

        Cowrie rotates cowrie.json (rename -> cowrie.json.<date>, then create a fresh
        file at the same path). A naive tailer that keeps one file handle and only
        seeks on truncation gets stuck on the OLD inode forever and never sees new
        events. This loop instead detects rotation via (device, inode) identity and
        RE-OPENS the current file at the path so freshly written events are always
        ingested. Reads are done in binary mode so byte offsets stay consistent with
        os.stat().st_size (text-mode tell() cookies are not comparable to raw sizes).
        """
        self._running = True
        self._stop_event.clear()

        logger.info("Starting AsyncLogCollector on %s (from_beginning=%s)", self.log_path, self.from_beginning)

        # Wait for the log file to be created if it does not exist yet at startup.
        while self._running and not self.log_path.exists():
            logger.debug("Waiting for log file to be created: %s", self.log_path)
            if await self._sleep_or_stop():
                break

        if not self._running:
            return

        first_open = True
        try:
            # Outer loop: (re)opens the file at the path. Each iteration binds to the
            # current inode, so a rotation simply causes us to re-open the new file.
            while self._running:
                try:
                    f = open(self.log_path, "rb")
                except FileNotFoundError:
                    # File momentarily absent mid-rotation; wait briefly and retry.
                    if await self._sleep_or_stop():
                        break
                    continue

                with f:
                    try:
                        st = os.fstat(f.fileno())
                        current_identity = self._file_identity(st)
                        file_size = st.st_size
                    except OSError:
                        current_identity = None
                        file_size = 0

                    # Only the very first open honours from_beginning=False (skip history).
                    # Every subsequent re-open (a rotation) starts at 0 so no line is missed.
                    offset = file_size if (first_open and not self.from_beginning) else 0
                    first_open = False
                    f.seek(offset)
                    self._buffer = ""
                    logger.info(
                        "AsyncLogCollector reading %s from offset %d (identity=%s)",
                        self.log_path, offset, current_identity,
                    )

                    # Inner loop: tails the currently open file handle.
                    while self._running:
                        chunk = f.read(65536)
                        if chunk:
                            self._buffer += chunk.decode("utf-8", errors="replace")
                            if "\n" in self._buffer:
                                lines = self._buffer.split("\n")
                                self._buffer = lines[-1]  # trailing partial line
                                for line in lines[:-1]:
                                    event = self._process_line(line)
                                    if event:
                                        await self._emit(event)
                            offset = f.tell()
                            continue

                        # No new data in this handle: check whether the path now points
                        # at a different file (rotation) or was truncated in place.
                        reopen = False
                        try:
                            path_st = os.stat(self.log_path)
                            path_identity = self._file_identity(path_st)
                            if current_identity is not None and path_identity != current_identity:
                                logger.info("Log rotation detected; re-opening %s", self.log_path)
                                reopen = True
                            elif path_st.st_size < offset:
                                logger.info("Log truncated in place; re-opening %s", self.log_path)
                                reopen = True
                        except OSError:
                            pass

                        if reopen:
                            break  # exit inner loop -> outer loop re-opens the file

                        if await self._sleep_or_stop():
                            break  # stop requested

                # Leave the outer loop when a stop was requested (not a rotation).
                if not self._running:
                    break

        except Exception as e:
            if self._running:
                logger.error("Unexpected error in log tailing loop: %s", e, exc_info=True)
        finally:
            self._running = False
            logger.info("AsyncLogCollector stopped.")

    def stop(self) -> None:
        """
        Signals the collector to terminate gracefully.
        """
        self._running = False
        self._stop_event.set()


def cli_main():
    """
    Command-line runner for the asynchronous log collector.
    """
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Cowrie Asynchronous Log Collector & Feature Extractor")
    parser.add_argument(
        "--log-path",
        default=os.getenv("COWRIE_LOG_PATH", "./honeypot/var/log/cowrie/cowrie.json"),
        help="Path to cowrie.json file (default: ./honeypot/var/log/cowrie/cowrie.json)"
    )
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        help="Process existing historical events from the beginning of the file"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    aggregator = SessionAggregator()
    collector = AsyncLogCollector(
        log_path=args.log_path,
        aggregator=aggregator,
        from_beginning=args.from_beginning
    )

    def print_event(event: NormalizedEvent, session: Any):
        print("\n" + "=" * 70)
        print("[EVENT INGESTED]")
        print(f"Event ID    : {event.event_id}")
        print(f"Session ID  : {event.session_id}")
        print(f"Source IP   : {event.source_ip or 'N/A'}")
        print(f"Event Type  : {event.event_type}")
        if event.command:
            print(f"Command     : {event.command}")
        if event.username:
            print(f"Username    : {event.username}")
        print(f"Timestamp   : {event.timestamp.isoformat()}")

        if session:
            print("-" * 70)
            print("[SESSION PROFILE UPDATE]")
            print(f"Session ID       : {session.session_id}")
            print(f"Duration (s)     : {session.duration_seconds}s")
            print(f"Total Events     : {session.total_events}")
            print(f"Commands Count   : {session.command_count} (Unique: {session.unique_command_count})")
            if session.commands:
                print(f"Recent Commands  : {', '.join(session.commands[-5:])}")
            if session.average_command_interval is not None:
                print(f"Avg Cmd Interval : {session.average_command_interval}s")
            print(f"Activity Rate    : {session.activity_rate} events/s")
            print(f"Session Closed   : {session.is_closed}")
        print("=" * 70 + "\n", flush=True)

    collector.register_callback(print_event)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def handle_sigint():
        print("\n[*] Stopping collector gracefully...")
        collector.stop()

    try:
        loop.run_until_complete(collector.start())
    except KeyboardInterrupt:
        collector.stop()
    finally:
        loop.close()


if __name__ == "__main__":
    cli_main()
