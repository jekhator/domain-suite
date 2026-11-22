"""Domain error defaults. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = [
    "DEFAULT_CODE",
    "DEFAULT_DOMAIN",
    "DEFAULT_HTTP_STATUS",
    "ERR_DOMAIN_UNSPECIFIED",
]


"""Base-class contract defaults; consumer subclasses override these per error type."""

DEFAULT_CODE: Final[str] = "domain_error"
DEFAULT_DOMAIN: Final[str] = "application"
DEFAULT_HTTP_STATUS: Final[int] = 500
ERR_DOMAIN_UNSPECIFIED: Final[str] = "An unspecified domain error occurred."
