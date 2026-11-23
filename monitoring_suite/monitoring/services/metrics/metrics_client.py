"""Metric sink protocol and implementations."""

from typing import Protocol

from monitoring_suite.monitoring.services.metrics import metrics_objects as objs


class MetricSink(Protocol):
    """Protocol for metric event sinks."""

    def emit(self, event: objs.MetricEvent) -> None:
        """Emit a metric event."""
        ...


class CollectingSink:
    """In-memory metric event collector for tests and development."""

    def __init__(self) -> None:
        """Initialize empty collector."""
        self._events: list[objs.MetricEvent] = []

    def emit(self, event: objs.MetricEvent) -> None:
        """Collect a metric event."""
        self._events.append(event)

    @property
    def events(self) -> list[objs.MetricEvent]:
        """Retrieve all collected events."""
        return self._events.copy()

    def clear(self) -> None:
        """Clear collected events."""
        self._events.clear()


class NullSink:
    """No-op sink for unbound monitoring."""

    def emit(self, event: objs.MetricEvent) -> None:
        """No-op emit."""
        pass
