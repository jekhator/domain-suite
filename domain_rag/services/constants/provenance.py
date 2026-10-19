"""Retrieval provenance validation constants. Imported as const."""

from __future__ import annotations

from typing import Final

ERR_PROVENANCE_QUERY_EMPTY: Final = "query must be non-empty"
ERR_PROVENANCE_PRINCIPAL_ID_EMPTY: Final = "principal_id must be non-empty"
ERR_PROVENANCE_SESSION_ID_EMPTY: Final = "session_id must be non-empty"
ERR_PROVENANCE_DURATION_NEGATIVE: Final = "duration_ms must be non-negative"
ERR_PROVENANCE_OCCURRED_AT_EMPTY: Final = "occurred_at must be non-empty"

NO_QUERY_PLACEHOLDER: Final = "(no query)"
NOTE_RECORDING_FAILED: Final = "provenance sink failed while recording a failed call"

QUERY_ARGUMENT: Final = "query"
RESULT_CHUNK_IDS_KEY: Final = "chunk_ids"
RESULT_SOURCE_IDS_KEY: Final = "source_document_ids"
