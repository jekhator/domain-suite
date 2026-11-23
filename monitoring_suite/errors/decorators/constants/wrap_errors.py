"""wrap_errors decorator constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Decorator markers and member-name conventions."""

WRAP_ERRORS_MARKER: Final[str] = "__wrap_errors_applied__"
PRIVATE_PREFIX: Final[str] = "_"


"""Messages and bound-argument names of the wrap_errors decorator."""

ERR_WRAP_ERRORS_INVALID_TARGET_PREFIX: Final[str] = "@wrap_errors target must be class or callable, got "
BOUND_SELF_NAME: Final[str] = "self"
BOUND_CLS_NAME: Final[str] = "cls"
