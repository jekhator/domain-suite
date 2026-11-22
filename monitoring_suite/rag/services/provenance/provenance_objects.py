"""Retrieval provenance event DTO. Frozen, hashable, immutable."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from monitoring_suite.rag.services.constants import provenance as const


class ProvenanceOutcome(StrEnum):
    """Retrieval provenance outcome enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class RetrievalProvenance:
    """Immutable retrieval provenance event with audit trail."""

    query: str
    chunk_ids: tuple[str, ...]
    source_document_ids: tuple[str, ...]
    principal_id: str
    session_id: str
    outcome: ProvenanceOutcome
    duration_ms: float
    occurred_at: str

    def __post_init__(self) -> None:
        """Validate retrieval provenance invariants."""
        if not self.query:
            raise ValueError(const.ERR_PROVENANCE_QUERY_EMPTY)
        if not self.principal_id:
            raise ValueError(const.ERR_PROVENANCE_PRINCIPAL_ID_EMPTY)
        if not self.session_id:
            raise ValueError(const.ERR_PROVENANCE_SESSION_ID_EMPTY)
        if self.duration_ms < 0:
            raise ValueError(const.ERR_PROVENANCE_DURATION_NEGATIVE)
        if not self.occurred_at:
            raise ValueError(const.ERR_PROVENANCE_OCCURRED_AT_EMPTY)

    @classmethod
    def for_success(
        cls, query: str, chunk_ids: tuple[str, ...], source_document_ids: tuple[str, ...],
        principal_id: str, session_id: str, duration_ms: float, occurred_at: str
    ) -> Self:
        """Create a success retrieval provenance event."""
        return cls(
            query=query, chunk_ids=chunk_ids, source_document_ids=source_document_ids, principal_id=principal_id,
            session_id=session_id, outcome=ProvenanceOutcome.SUCCESS, duration_ms=duration_ms, occurred_at=occurred_at
        )

    @classmethod
    def for_failure(cls, query: str, principal_id: str, session_id: str, duration_ms: float, occurred_at: str) -> Self:
        """Create a failure retrieval provenance event."""
        return cls(
            query=query, chunk_ids=(), source_document_ids=(), principal_id=principal_id, session_id=session_id,
            outcome=ProvenanceOutcome.FAILURE, duration_ms=duration_ms, occurred_at=occurred_at
        )

    @property
    def is_failure(self) -> bool:
        """Check if provenance represents a failure."""
        return self.outcome == ProvenanceOutcome.FAILURE
