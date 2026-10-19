"""Provenance sink protocol and implementations."""

from typing import Protocol

from domain_rag.services.provenance.provenance_objects import RetrievalProvenance


class ProvenanceSink(Protocol):
    """Protocol for retrieval provenance event sinks."""

    def record(self, event: RetrievalProvenance) -> None:
        """Record a retrieval provenance event."""
        ...


class CollectingProvenanceSink:
    """In-memory provenance event collector for tests and development."""

    def __init__(self) -> None:
        """Initialize empty collector."""
        self._events: list[RetrievalProvenance] = []

    def record(self, event: RetrievalProvenance) -> None:
        """Collect a retrieval provenance event."""
        self._events.append(event)

    @property
    def events(self) -> list[RetrievalProvenance]:
        """Retrieve all collected events."""
        return self._events.copy()

    def clear(self) -> None:
        """Clear collected events."""
        self._events.clear()


class NullProvenanceSink:
    """No-op sink for unbound retrieval provenance."""

    def record(self, event: RetrievalProvenance) -> None:
        """No-op record."""
