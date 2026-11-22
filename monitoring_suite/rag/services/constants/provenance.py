"""Retrieval provenance validation constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Retrieval provenance validation error messages."""

ERR_PROVENANCE_QUERY_EMPTY: Final[str] = "query must be non-empty"
ERR_PROVENANCE_PRINCIPAL_ID_EMPTY: Final[str] = "principal_id must be non-empty"
ERR_PROVENANCE_SESSION_ID_EMPTY: Final[str] = "session_id must be non-empty"
ERR_PROVENANCE_DURATION_NEGATIVE: Final[str] = "duration_ms must be non-negative"
ERR_PROVENANCE_OCCURRED_AT_EMPTY: Final[str] = "occurred_at must be non-empty"


"""Retrieval call and result keys, and unit conversion."""

KWARG_QUERY: Final[str] = "query"
RESULT_KEY_CHUNK_IDS: Final[str] = "chunk_ids"
RESULT_KEY_SOURCE_DOCUMENT_IDS: Final[str] = "source_document_ids"
MILLISECONDS_PER_SECOND: Final[int] = 1000


"""Decorator markers and member-name conventions."""

PRIVATE_PREFIX: Final[str] = "_"
ATTR_BASES: Final[str] = "__bases__"


"""Enumeration member values."""

OUTCOME_SUCCESS: Final[str] = "success"
OUTCOME_FAILURE: Final[str] = "failure"
