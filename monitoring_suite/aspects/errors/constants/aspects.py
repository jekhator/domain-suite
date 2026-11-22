"""
Error messages raised at the API surface (source-side; tests match against these via const.ERR_*).

Imported as const.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ERR_ASPECTS_COMPOSITION_FAILED",
    "ERR_ASPECTS_DECLARATION_FAILED",
    "ERR_ASPECTS_DUPLICATE_KIND",
    "ERR_ASPECTS_UNKNOWN_ENTRY_TYPE",
    "ERR_ASPECTS_EMPTY_DECLARATION",
]


"""Aspect composition error messages."""

ERR_ASPECTS_COMPOSITION_FAILED: Final[str] = "Aspect composition failed."

ERR_ASPECTS_DECLARATION_FAILED: Final[str] = "Aspect declaration failed."


"""Aspect declaration validation error messages."""

ERR_ASPECTS_DUPLICATE_KIND: Final[str] = "Duplicate aspect kind in declaration: {kind}."

ERR_ASPECTS_UNKNOWN_ENTRY_TYPE: Final[str] = "Unknown aspect entry type: {entry_type}."

ERR_ASPECTS_EMPTY_DECLARATION: Final[str] = "Aspect declaration is empty."
