"""HTTP classifier domain name and recognized libraries. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = [
    "HTTP",
    "HTTP_LIBRARIES",
]


"""HTTP-layer domain the classifier maps httpx/requests/aiohttp errors to."""

HTTP: Final = "http"


"""Top-level package names of the HTTP-client libraries classified by origin."""

HTTP_LIBRARIES: Final = frozenset({"httpx", "requests", "aiohttp"})
