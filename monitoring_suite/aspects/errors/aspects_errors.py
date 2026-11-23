"""Typed aspect composition error hierarchy."""

from __future__ import annotations

from monitoring_suite.aspects.errors.constants import aspects as const
from monitoring_suite.errors import DomainError


class AspectsError(DomainError):
    """Base error for all aspect-composition failures."""

    domain = const.DOMAIN_ASPECTS
    code = const.CODE_ASPECTS_ERROR
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_ASPECTS_COMPOSITION_FAILED


class AspectDeclarationError(AspectsError):
    """Decorator declaration-time validation failure."""

    code = const.CODE_ASPECT_DECLARATION_FAILED
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_ASPECTS_DECLARATION_FAILED
