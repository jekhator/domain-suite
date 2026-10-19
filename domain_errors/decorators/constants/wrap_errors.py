"""@wrap_errors constants. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = [
    "ERR_WRAP_ERRORS_TARGET_TYPE",
    "WRAP_ERRORS_MARKER",
]


"""Attribute stamped on every callable that @wrap_errors has decorated."""

WRAP_ERRORS_MARKER: Final = "__wrap_errors_applied__"


"""Message prefix for a decoration target that is neither a class nor a callable."""

ERR_WRAP_ERRORS_TARGET_TYPE: Final = (
    "@wrap_errors target must be class or callable, got"
)
