"""Typed rate-limit error hierarchy for declaration and enforcement mapping."""

from __future__ import annotations

from monitoring_suite.api_limiter.errors.constants import api_limiter_errors as const
from monitoring_suite.errors import DomainError


class ThrottleError(DomainError):
    """Base error for all rate-limit domain failures."""

    domain = "api_limiter"
    code = "throttle_error"
    http_status = 429
    retryable = True
    default_message = const.ERR_API_LIMITER_CONSTRAINT_VIOLATED


class RateLimitExceeded(ThrottleError):
    """Request rejected because a rate limit was exceeded."""

    code = "rate_limit_exceeded"
    default_message = const.ERR_API_LIMITER_RATE_EXCEEDED


class ThrottleDeclarationError(ThrottleError):
    """Invalid throttle declaration detected at import time."""

    code = "throttle_declaration_invalid"
    http_status = 500
    retryable = False
    default_message = const.ERR_API_LIMITER_DECLARATION_INVALID
