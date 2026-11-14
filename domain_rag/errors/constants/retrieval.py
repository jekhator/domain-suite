"""Retrieval error messages. Imported as const."""

from typing import Final

# Retrieval failures.
ERR_RETRIEVAL_FAILED: Final = "Retrieval operation failed"

# Invalid decorator targets.
ERR_RETRIEVAL_INVALID_TARGET: Final = (
    "Invalid retrieval target: must be a callable or class"
)

# Empty class decoration.
ERR_RETRIEVAL_EMPTY_CLASS: Final = "Cannot trace class with no public methods"

# Missing decorator identity.
ERR_RETRIEVAL_EMPTY_PRINCIPAL: Final = "Retrieval principal_id must be non-empty"
ERR_RETRIEVAL_EMPTY_SESSION: Final = "Retrieval session_id must be non-empty"
