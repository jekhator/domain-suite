"""Aspects service: composable decorator stacking."""

from __future__ import annotations

from monitoring_suite.aspects.services.aspects.aspects_client import aspects
from monitoring_suite.aspects.services.aspects.aspects_objects import (
    AspectEntry,
    AspectKind,
    Logged,
    RequireMixins,
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
    "RequireMixins",
    "Requires",
    "Retried",
    "TenantScoped",
    "Throttled",
    "WrapErrors",
]
