"""Retrieval provenance validation constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Retrieval provenance validation error messages."""

ERR_PROVENANCE_QUERY_EMPTY: Final[str] = "query must be non-empty"
ERR_PROVENANCE_PRINCIPAL_ID_EMPTY: Final[str] = "principal_id must be non-empty"
ERR_PROVENANCE_SESSION_ID_EMPTY: Final[str] = "session_id must be non-empty"
ERR_PROVENANCE_DURATION_NEGATIVE: Final[str] = "duration_ms must be non-negative"
ERR_PROVENANCE_OCCURRED_AT_EMPTY: Final[str] = "occurred_at must be non-empty"
