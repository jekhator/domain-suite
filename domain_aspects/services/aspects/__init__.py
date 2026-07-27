"""Aspects service: composable decorator stacking."""

from __future__ import annotations

from domain_aspects.services.aspects.aspects_client import aspects
from domain_aspects.services.aspects.aspects_objects import (
    AspectEntry,
    AspectKind,
    Logged,
    Requires,
    Retried,
    TenantScoped,
    Throttled,
    WrapErrors,
)

__all__ = [
    "aspects",
    "AspectEntry",
    "AspectKind",
    "Logged",
    "Requires",
    "Retried",
    "TenantScoped",
    "Throttled",
    "WrapErrors",
]
