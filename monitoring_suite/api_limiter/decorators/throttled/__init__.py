"""Rate-limit declaration decorator."""

from monitoring_suite.api_limiter.decorators.throttled.throttled_client import Throttled, throttled

__all__ = ["Throttled", "throttled"]
