"""Stdlib classifier domain names. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = [
    "ASSERTION",
    "LOGIC",
    "NETWORK",
    "OS",
]


"""Coarse domains the stdlib classifier maps exception families to."""

ASSERTION: Final[str] = "assertion"
LOGIC: Final[str] = "logic"
NETWORK: Final[str] = "network"
OS: Final[str] = "os"
