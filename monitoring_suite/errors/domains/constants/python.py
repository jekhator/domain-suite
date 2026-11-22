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

ASSERTION: Final = "assertion"
LOGIC: Final = "logic"
NETWORK: Final = "network"
OS: Final = "os"
