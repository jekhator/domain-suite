"""Error-chaining constants. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = ["ATTR_CODE", "ATTR_CONTEXT", "ATTR_DOMAIN", "DEFAULT_DOMAIN", "VIA_CAUSE", "VIA_CONTEXT", "VIA_ROOT"]


"""Domain assigned to an error when no classvar or classifier resolves it."""

DEFAULT_DOMAIN: Final[str] = "python"


"""Attribute names read from errors by name."""

ATTR_DOMAIN: Final[str] = "domain"
ATTR_CODE: Final[str] = "code"
ATTR_CONTEXT: Final[str] = "context"


"""Enumeration member values."""

VIA_ROOT: Final[str] = "root"
VIA_CAUSE: Final[str] = "cause"
VIA_CONTEXT: Final[str] = "context"
