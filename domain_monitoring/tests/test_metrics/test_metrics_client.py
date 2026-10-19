"""Tests for MetricSink protocol and implementations."""

from domain_monitoring.services.metrics.metrics_client import CollectingSink, NullSink
from domain_monitoring.services.metrics.metrics_objects import MetricEvent, Outcome


class TestCollectingSink:
    """CollectingSink for testing and development."""

    def test_emit_collects_event(self) -> None:
        """Emit stores event in collection."""
        sink = CollectingSink()
        event = MetricEvent(
            event="test.method",
            outcome=Outcome.SUCCESS,
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        sink.emit(event)

        assert len(sink.events) == 1
        assert sink.events[0] == event

    def test_multiple_emits(self) -> None:
        """Emit can be called multiple times."""
        sink = CollectingSink()
        event1 = MetricEvent.for_success("test.method1", 50.0, "2026-07-07T12:00:00Z")
        event2 = MetricEvent.for_failure("test.method2", 75.0, "2026-07-07T12:00:01Z")

        sink.emit(event1)
        sink.emit(event2)

        assert len(sink.events) == 2
        assert sink.events[0] == event1
        assert sink.events[1] == event2

    def test_events_returns_copy(self) -> None:
        """Events property returns copy, not reference."""
        sink = CollectingSink()
        event = MetricEvent.for_success("test.method", 100.0, "2026-07-07T12:00:00Z")
        sink.emit(event)

        events_copy = sink.events
        events_copy.append(
            MetricEvent.for_failure("test.other", 50.0, "2026-07-07T12:00:01Z")
        )

        assert len(sink.events) == 1

    def test_clear_empties_collection(self) -> None:
        """Clear removes all events."""
        sink = CollectingSink()
        sink.emit(MetricEvent.for_success("test.method", 100.0, "2026-07-07T12:00:00Z"))
        sink.emit(MetricEvent.for_failure("test.other", 50.0, "2026-07-07T12:00:01Z"))

        assert len(sink.events) == 2

        sink.clear()

        assert len(sink.events) == 0


class TestNullSink:
    """NullSink for unbound monitoring."""

    def test_emit_is_noop(self) -> None:
        """Emit does nothing."""
        sink = NullSink()
        event = MetricEvent.for_success("test.method", 100.0, "2026-07-07T12:00:00Z")

        sink.emit(event)

        assert vars(sink) == {}
