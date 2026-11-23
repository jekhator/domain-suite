"""
Error messages raised at the API surface (source-side; tests match against these via const.ERR_*).

Imported as const.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CODE_ASPECTS_ERROR", "CODE_ASPECT_DECLARATION_FAILED", "DOMAIN_ASPECTS",
    "ERR_ASPECTS_COMPOSITION_FAILED", "ERR_ASPECTS_DECLARATION_FAILED", "ERR_ASPECTS_DUPLICATE_KIND",
    "ERR_ASPECTS_UNKNOWN_ENTRY_TYPE", "ERR_ASPECTS_EMPTY_DECLARATION", "HTTP_STATUS_INTERNAL_SERVER_ERROR"
]


"""Aspect composition error messages."""

ERR_ASPECTS_COMPOSITION_FAILED: Final[str] = "Aspect composition failed."

ERR_ASPECTS_DECLARATION_FAILED: Final[str] = "Aspect declaration failed."


"""Aspect declaration validation error messages."""

ERR_ASPECTS_DUPLICATE_KIND: Final[str] = "Duplicate aspect kind in declaration: {kind}."

ERR_ASPECTS_UNKNOWN_ENTRY_TYPE: Final[str] = "Unknown aspect entry type: {entry_type}."

ERR_ASPECTS_EMPTY_DECLARATION: Final[str] = "Aspect declaration is empty."


"""Error class contract values: domain, codes and HTTP statuses."""

DOMAIN_ASPECTS: Final[str] = "aspects"
CODE_ASPECTS_ERROR: Final[str] = "aspects_error"
HTTP_STATUS_INTERNAL_SERVER_ERROR: Final[int] = 500
CODE_ASPECT_DECLARATION_FAILED: Final[str] = "aspect_declaration_failed"
