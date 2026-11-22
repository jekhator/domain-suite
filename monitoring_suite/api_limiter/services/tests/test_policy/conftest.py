"""Fixtures for policy tests."""

from __future__ import annotations

import pytest

from monitoring_suite.api_limiter.services.policy.policy_client import PolicyRegistry
from monitoring_suite.api_limiter.services.policy.policy_objects import Period, RateLimit, ThrottlePolicy, TierRate


@pytest.fixture
def rate_limit_100_per_hour() -> RateLimit:  # noqa: R004
    """
    A rate limit of 100 requests per hour.

    Used by: no test class yet.
    """
    return RateLimit(requests=100, period=Period.HOUR)


@pytest.fixture
def rate_limit_1000_per_day() -> RateLimit:  # noqa: R004
    """
    A rate limit of 1000 requests per day.

    Used by: no test class yet.
    """
    return RateLimit(requests=1000, period=Period.DAY)


@pytest.fixture
def rate_limit_5_per_second() -> RateLimit:  # noqa: R004
    """
    A rate limit of 5 requests per second.

    Used by: no test class yet.
    """
    return RateLimit(requests=5, period=Period.SECOND)


@pytest.fixture
def tier_rate_premium() -> TierRate:  # noqa: R004
    """
    A premium tier rate of 500 per hour.

    Used by: no test class yet.
    """
    rate = RateLimit(requests=500, period=Period.HOUR)
    return TierRate(tier="premium", rate=rate)


@pytest.fixture
def tier_rate_enterprise() -> TierRate:  # noqa: R004
    """
    An enterprise tier rate of 10000 per hour.

    Used by: no test class yet.
    """
    rate = RateLimit(requests=10000, period=Period.HOUR)
    return TierRate(tier="enterprise", rate=rate)


@pytest.fixture
def throttle_policy_base() -> ThrottlePolicy:  # noqa: R004
    """
    A throttle policy with only base rate.

    Used by: no test class yet.
    """
    rate = RateLimit(requests=100, period=Period.HOUR)
    return ThrottlePolicy(scope="api.users.list", rate=rate)


@pytest.fixture
def throttle_policy_with_tiers(  # noqa: R004
    tier_rate_premium: TierRate, tier_rate_enterprise: TierRate
) -> ThrottlePolicy:
    """
    A throttle policy with base rate and tier overrides.

    Used by: no test class yet.
    """
    rate = RateLimit(requests=10, period=Period.HOUR)
    return ThrottlePolicy(scope="api.data.export", rate=rate, tier_rates=(tier_rate_premium, tier_rate_enterprise))


@pytest.fixture
def registry() -> PolicyRegistry:  # noqa: R004
    """
    A policy registry instance.

    Used by: TestPolicyRegistry.
    """
    return PolicyRegistry()
