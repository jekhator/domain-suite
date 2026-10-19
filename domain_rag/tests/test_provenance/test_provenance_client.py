"""Tests for ProvenanceSink protocol and implementations."""

from domain_rag.services.provenance.provenance_client import (
    CollectingProvenanceSink,
    NullProvenanceSink,
)
from domain_rag.services.provenance.provenance_objects import (
    ProvenanceOutcome,
    RetrievalProvenance,
)


class TestCollectingProvenanceSink:
    """CollectingProvenanceSink for testing and development."""

    def test_record_collects_event(self) -> None:
        """Record stores event in collection."""
        sink = CollectingProvenanceSink()
        event = RetrievalProvenance(
            query="query",
            chunk_ids=("c1",),
            source_document_ids=("d1",),
            principal_id="p1",
            session_id="s1",
            outcome=ProvenanceOutcome.SUCCESS,
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        sink.record(event)

        assert len(sink.events) == 1
        assert sink.events[0] == event

    def test_multiple_records(self) -> None:
        """Record can be called multiple times."""
        sink = CollectingProvenanceSink()
        event1 = RetrievalProvenance.for_success(
            query="q1",
            chunk_ids=("c1",),
            source_document_ids=("d1",),
            principal_id="p1",
            session_id="s1",
            duration_ms=50.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        event2 = RetrievalProvenance.for_failure(
            query="q2",
            principal_id="p1",
            session_id="s1",
            duration_ms=75.0,
            occurred_at="2026-07-07T12:00:01Z",
        )

        sink.record(event1)
        sink.record(event2)

        assert len(sink.events) == 2
        assert sink.events[0] == event1
        assert sink.events[1] == event2

    def test_events_returns_copy(self) -> None:
        """Events property returns copy, not reference."""
        sink = CollectingProvenanceSink()
        event = RetrievalProvenance.for_success(
            query="q",
            chunk_ids=(),
            source_document_ids=(),
            principal_id="p1",
            session_id="s1",
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        sink.record(event)

        events_copy = sink.events
        events_copy.append(
            RetrievalProvenance.for_failure(
                query="q2",
                principal_id="p1",
                session_id="s1",
                duration_ms=50.0,
                occurred_at="2026-07-07T12:00:01Z",
            )
        )

        assert len(sink.events) == 1

    def test_clear_empties_collection(self) -> None:
        """Clear removes all events."""
        sink = CollectingProvenanceSink()
        sink.record(
            RetrievalProvenance.for_success(
                query="q1",
                chunk_ids=(),
                source_document_ids=(),
                principal_id="p1",
                session_id="s1",
                duration_ms=100.0,
                occurred_at="2026-07-07T12:00:00Z",
            )
        )
        sink.record(
            RetrievalProvenance.for_failure(
                query="q2",
                principal_id="p1",
                session_id="s1",
                duration_ms=50.0,
                occurred_at="2026-07-07T12:00:01Z",
            )
        )

        assert len(sink.events) == 2

        sink.clear()

        assert len(sink.events) == 0


class TestNullProvenanceSink:
    """NullProvenanceSink for unbound retrieval provenance."""

    def test_record_is_noop(self) -> None:
        """Record does nothing."""
        sink = NullProvenanceSink()
        event = RetrievalProvenance.for_success(
            query="q",
            chunk_ids=(),
            source_document_ids=(),
            principal_id="p1",
            session_id="s1",
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        sink.record(event)

        assert vars(sink) == {}
