"""Domain aspects: composable cross-cutting decorators for any service."""

from __future__ import annotations

from domain_aspects.config._version import __version__
from domain_aspects.errors.aspects_errors import (
    AspectDeclarationError,
    AspectsError,
)
from domain_aspects.services.aspects.aspects_client import aspects
from domain_aspects.services.aspects.aspects_objects import (
    AspectEntry,
    AspectKind,
    Logged,
    Monitored,
    Requires,
    Retried,
    TenantScoped,
    Throttled,
    WrapErrors,
)
from domain_aspects.services.aspects.aspects_require_mixins import RequireMixins
from domain_aspects.services.constants.aspects import ASPECT_ORDER

__all__ = [
    "ASPECT_ORDER",
    "AspectDeclarationError",
    "AspectEntry",
    "AspectKind",
    "AspectsError",
    "Logged",
    "Monitored",
    "RequireMixins",
    "Requires",
    "Retried",
    "TenantScoped",
    "Throttled",
    "WrapErrors",
    "__version__",
    "aspects",
]
