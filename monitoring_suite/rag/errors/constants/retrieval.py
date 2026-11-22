"""Retrieval error messages. Imported as const."""

from typing import Final

"""Retrieval failures."""

ERR_RETRIEVAL_FAILED: Final[str] = "Retrieval operation failed"

"""Invalid decorator targets."""

ERR_RETRIEVAL_INVALID_TARGET: Final[str] = (
    "Invalid retrieval target: must be a callable or class"
)

"""Empty class decoration."""

ERR_RETRIEVAL_EMPTY_CLASS: Final[str] = "Cannot trace class with no public methods"
