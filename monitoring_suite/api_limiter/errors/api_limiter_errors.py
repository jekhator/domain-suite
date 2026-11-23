"""Typed rate-limit error hierarchy for declaration and enforcement mapping."""

from __future__ import annotations

from monitoring_suite.api_limiter.errors.constants import api_limiter_errors as const
from monitoring_suite.errors import DomainError


class ThrottleError(DomainError):
    """Base error for all rate-limit domain failures."""

    domain = const.DOMAIN_API_LIMITER
    code = const.CODE_THROTTLE_ERROR
    http_status = const.HTTP_STATUS_TOO_MANY_REQUESTS
    retryable = True
    default_message = const.ERR_API_LIMITER_CONSTRAINT_VIOLATED


class RateLimitExceeded(ThrottleError):
    """Request rejected because a rate limit was exceeded."""

    code = const.CODE_RATE_LIMIT_EXCEEDED
    default_message = const.ERR_API_LIMITER_RATE_EXCEEDED


class ThrottleDeclarationError(ThrottleError):
    """Invalid throttle declaration detected at import time."""

    code = const.CODE_THROTTLE_DECLARATION_INVALID
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_API_LIMITER_DECLARATION_INVALID
