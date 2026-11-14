"""Tests for RetrievalProvenance DTO."""

import dataclasses

import pytest

from domain_rag.services.constants import provenance as const
from domain_rag.services.provenance.provenance_objects import (
    ProvenanceOutcome,
    RetrievalProvenance,
)


class TestProvenanceOutcome:
    """ProvenanceOutcome enumeration."""

    def test_success_value(self) -> None:
        """SUCCESS has correct string value."""
        assert ProvenanceOutcome.SUCCESS == "success"

    def test_failure_value(self) -> None:
        """FAILURE has correct string value."""
        assert ProvenanceOutcome.FAILURE == "failure"


class TestRetrievalProvenanceCreation:
    """RetrievalProvenance creation and validation."""

    def test_retrieval_provenance_creation(self) -> None:
        """Create a RetrievalProvenance successfully."""
        provenance = RetrievalProvenance(
            query="what is accessibility?",
            chunk_ids=("chunk1", "chunk2"),
            source_document_ids=("doc1", "doc2"),
            principal_id="user_123",
            session_id="sess_456",
            outcome=ProvenanceOutcome.SUCCESS,
            duration_ms=50.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert provenance.query == "what is accessibility?"
        assert provenance.chunk_ids == ("chunk1", "chunk2")
        assert provenance.source_document_ids == ("doc1", "doc2")
        assert provenance.principal_id == "user_123"
        assert provenance.session_id == "sess_456"
        assert provenance.outcome == ProvenanceOutcome.SUCCESS
        assert provenance.duration_ms == 50.0
        assert provenance.occurred_at == "2026-07-07T12:00:00Z"

    def test_retrieval_provenance_immutable(self) -> None:
        """RetrievalProvenance is frozen (immutable)."""
        provenance = RetrievalProvenance(
            query="query",
            chunk_ids=("c1",),
            source_document_ids=("d1",),
            principal_id="p1",
            session_id="s1",
            outcome=ProvenanceOutcome.SUCCESS,
            duration_ms=10.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            provenance.query = "modified"  # type: ignore[misc]

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"query": ""}, const.ERR_PROVENANCE_QUERY_EMPTY),
            ({"principal_id": ""}, const.ERR_PROVENANCE_PRINCIPAL_ID_EMPTY),
            ({"session_id": ""}, const.ERR_PROVENANCE_SESSION_ID_EMPTY),
            ({"duration_ms": -5.0}, const.ERR_PROVENANCE_DURATION_NEGATIVE),
            ({"occurred_at": ""}, const.ERR_PROVENANCE_OCCURRED_AT_EMPTY),
        ],
    )
    def test_invalid_field_raises(
        self, overrides: dict[str, object], message: str
    ) -> None:
        """Each invalid field raises ValueError with its constant message."""
        fields: dict[str, object] = {
            "query": "query",
            "chunk_ids": (),
            "source_document_ids": (),
            "principal_id": "p1",
            "session_id": "s1",
            "outcome": ProvenanceOutcome.SUCCESS,
            "duration_ms": 10.0,
            "occurred_at": "2026-07-07T12:00:00Z",
            **overrides,
        }

        with pytest.raises(ValueError, match=message):
            RetrievalProvenance(**fields)  # type: ignore[arg-type]


class TestRetrievalProvenanceFactories:
    """RetrievalProvenance factory methods."""

    def test_for_success_creates_success_event(self) -> None:
        """for_success creates SUCCESS provenance."""
        provenance = RetrievalProvenance.for_success(
            query="query",
            chunk_ids=("c1", "c2"),
            source_document_ids=("d1",),
            principal_id="p1",
            session_id="s1",
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert provenance.query == "query"
        assert provenance.chunk_ids == ("c1", "c2")
        assert provenance.source_document_ids == ("d1",)
        assert provenance.principal_id == "p1"
        assert provenance.session_id == "s1"
        assert provenance.outcome == ProvenanceOutcome.SUCCESS
        assert provenance.duration_ms == 100.0
        assert provenance.occurred_at == "2026-07-07T12:00:00Z"

    def test_for_failure_creates_failure_event(self) -> None:
        """for_failure creates FAILURE provenance with empty chunks."""
        provenance = RetrievalProvenance.for_failure(
            query="query",
            principal_id="p1",
            session_id="s1",
            duration_ms=50.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert provenance.query == "query"
        assert provenance.chunk_ids == ()
        assert provenance.source_document_ids == ()
        assert provenance.principal_id == "p1"
        assert provenance.session_id == "s1"
        assert provenance.outcome == ProvenanceOutcome.FAILURE
        assert provenance.duration_ms == 50.0
        assert provenance.occurred_at == "2026-07-07T12:00:00Z"


class TestRetrievalProvenanceProperties:
    """RetrievalProvenance properties and methods."""

    def test_is_failure_for_success(self) -> None:
        """is_failure returns False for success outcome."""
        provenance = RetrievalProvenance.for_success(
            query="q",
            chunk_ids=(),
            source_document_ids=(),
            principal_id="p",
            session_id="s",
            duration_ms=1.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        assert not provenance.is_failure

    def test_is_failure_for_failure(self) -> None:
        """is_failure returns True for failure outcome."""
        provenance = RetrievalProvenance.for_failure(
            query="q",
            principal_id="p",
            session_id="s",
            duration_ms=1.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        assert provenance.is_failure

    def test_hash_consistency(self) -> None:
        """Hash is consistent for identical provenances."""
        provenance1 = RetrievalProvenance(
            query="query",
            chunk_ids=("c1",),
            source_document_ids=("d1",),
            principal_id="p1",
            session_id="s1",
            outcome=ProvenanceOutcome.SUCCESS,
            duration_ms=50.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        provenance2 = RetrievalProvenance(
            query="query",
            chunk_ids=("c1",),
            source_document_ids=("d1",),
            principal_id="p1",
            session_id="s1",
            outcome=ProvenanceOutcome.SUCCESS,
            duration_ms=50.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert hash(provenance1) == hash(provenance2)

    def test_hash_differs_for_different_outcomes(self) -> None:
        """Hash differs for different outcomes."""
        success = RetrievalProvenance.for_success(
            query="q",
            chunk_ids=(),
            source_document_ids=(),
            principal_id="p",
            session_id="s",
            duration_ms=1.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        failure = RetrievalProvenance.for_failure(
            query="q",
            principal_id="p",
            session_id="s",
            duration_ms=1.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert hash(success) != hash(failure)

    def test_zero_duration_valid(self) -> None:
        """Zero duration is valid (edge case boundary)."""
        provenance = RetrievalProvenance.for_success(
            query="q",
            chunk_ids=(),
            source_document_ids=(),
            principal_id="p",
            session_id="s",
            duration_ms=0.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        assert provenance.duration_ms == 0.0

    def test_empty_chunks_and_sources_valid(self) -> None:
        """Empty chunk and source tuples are valid."""
        provenance = RetrievalProvenance.for_success(
            query="q",
            chunk_ids=(),
            source_document_ids=(),
            principal_id="p",
            session_id="s",
            duration_ms=10.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        assert provenance.chunk_ids == ()
        assert provenance.source_document_ids == ()
