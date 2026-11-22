"""Domain aspects: composable cross-cutting decorators for any service."""

from __future__ import annotations

from monitoring_suite.aspects.config._version import __version__
from monitoring_suite.aspects.errors.aspects_errors import AspectDeclarationError, AspectsError
from monitoring_suite.aspects.services.aspects.aspects_client import aspects
from monitoring_suite.aspects.services.aspects.aspects_objects import (
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
from monitoring_suite.aspects.services.aspects.aspects_require_mixins import RequireMixins
from monitoring_suite.aspects.services.constants.aspects import ASPECT_ORDER

__all__ = [
    "__version__", "ASPECT_ORDER", "aspects", "AspectEntry", "AspectKind", "AspectsError", "AspectDeclarationError",
    "Logged", "Monitored", "RequireMixins", "Requires", "Retried", "TenantScoped", "Throttled", "WrapErrors"
]
