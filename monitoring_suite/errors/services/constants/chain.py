"""Error-chaining constants. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = [
    "DEFAULT_DOMAIN",
]


"""Domain assigned to an error when no classvar or classifier resolves it."""

DEFAULT_DOMAIN: Final = "python"
