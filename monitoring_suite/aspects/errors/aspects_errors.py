"""Typed aspect composition error hierarchy."""

from __future__ import annotations

from monitoring_suite.aspects.errors.constants import aspects as const
from monitoring_suite.errors import DomainError


class AspectsError(DomainError):
    """Base error for all aspect-composition failures."""

    domain = "aspects"
    code = "aspects_error"
    http_status = 500
    retryable = False
    default_message = const.ERR_ASPECTS_COMPOSITION_FAILED


class AspectDeclarationError(AspectsError):
    """Decorator declaration-time validation failure."""

    code = "aspect_declaration_failed"
    http_status = 500
    retryable = False
    default_message = const.ERR_ASPECTS_DECLARATION_FAILED
