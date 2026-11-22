"""Rate-limit declaration toolkit for Python services."""

from monitoring_suite.api_limiter.config._version import __version__
from monitoring_suite.api_limiter.decorators.throttled.throttled_client import throttled
from monitoring_suite.api_limiter.errors.api_limiter_errors import (
    RateLimitExceeded,
    ThrottleDeclarationError,
    ThrottleError,
)
from monitoring_suite.api_limiter.services.policy.policy_client import PolicyRegistry
from monitoring_suite.api_limiter.services.policy.policy_objects import (
    Period,
    RateLimit,
    ThrottlePolicy,
    TierRate,
)

__all__ = [
    "Period",
    "PolicyRegistry",
    "RateLimit",
    "RateLimitExceeded",
    "ThrottleDeclarationError",
    "ThrottleError",
    "ThrottlePolicy",
    "TierRate",
    "__version__",
    "throttled",
]
