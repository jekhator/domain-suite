"""Tests for policy value objects."""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError

import pytest

from domain_api_limiter.errors.api_limiter_errors import ThrottleDeclarationError
from domain_api_limiter.services.constants import policy as const
from domain_api_limiter.services.policy.policy_objects import (
    Period,
    RateLimit,
    ThrottlePolicy,
    TierRate,
)


class TestPeriod:
    """Period is a rate period vocabulary."""

    def test_period_second_value(self) -> None:
        """Period.SECOND has value 'second'."""
        assert Period.SECOND.value == "second"

    def test_period_minute_value(self) -> None:
        """Period.MINUTE has value 'minute'."""
        assert Period.MINUTE.value == "minute"

    def test_period_hour_value(self) -> None:
        """Period.HOUR has value 'hour'."""
        assert Period.HOUR.value == "hour"

    def test_period_day_value(self) -> None:
        """Period.DAY has value 'day'."""
        assert Period.DAY.value == "day"

    def test_period_all_members(self) -> None:
        """Period has all four members."""
        members = list(Period)
        assert len(members) == 4
        assert Period.SECOND in members
        assert Period.MINUTE in members
        assert Period.HOUR in members
        assert Period.DAY in members


class TestRateLimit:
    """RateLimit is a parsed rate with request count and period."""

    def test_valid_rate_limit_creation(self) -> None:
        """RateLimit accepts positive request count and period."""
        rate = RateLimit(requests=100, period=Period.HOUR)
        assert rate.requests == 100
        assert rate.period == Period.HOUR

    def test_from_rate_100_per_hour(self) -> None:
        """RateLimit.from_rate parses '100/hour'."""
        rate = RateLimit.from_rate("100/hour")
        assert rate.requests == 100
        assert rate.period == Period.HOUR

    def test_from_rate_1_per_second(self) -> None:
        """RateLimit.from_rate parses '1/second'."""
        rate = RateLimit.from_rate("1/second")
        assert rate.requests == 1
        assert rate.period == Period.SECOND

    def test_from_rate_10000_per_day(self) -> None:
        """RateLimit.from_rate parses '10000/day'."""
        rate = RateLimit.from_rate("10000/day")
        assert rate.requests == 10000
        assert rate.period == Period.DAY

    def test_from_rate_60_per_minute(self) -> None:
        """RateLimit.from_rate parses '60/minute'."""
        rate = RateLimit.from_rate("60/minute")
        assert rate.requests == 60
        assert rate.period == Period.MINUTE

    def test_from_rate_missing_slash(self) -> None:
        """RateLimit.from_rate rejects rate without slash."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_RATE_FORMAT),
        ) as exc_info:
            RateLimit.from_rate("100hour")
        assert exc_info.value.context.get("rate") == "100hour"

    def test_from_rate_non_digit_head(self) -> None:
        """RateLimit.from_rate rejects non-digit before slash."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_RATE_FORMAT),
        ) as exc_info:
            RateLimit.from_rate("x/hour")
        assert exc_info.value.context.get("rate") == "x/hour"

    def test_from_rate_unknown_period(self) -> None:
        """RateLimit.from_rate rejects unknown period with __cause__ ValueError."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_UNKNOWN_PERIOD),
        ) as exc_info:
            RateLimit.from_rate("10/fortnight")
        assert exc_info.value.context.get("rate") == "10/fortnight"
        assert exc_info.value.context.get("period") == "fortnight"
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_from_rate_superscript_digit_head(self) -> None:
        """RateLimit.from_rate rejects superscript digits that int() cannot parse."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_RATE_FORMAT),
        ) as exc_info:
            RateLimit.from_rate("\u00b2/hour")
        assert exc_info.value.context.get("rate") == "\u00b2/hour"

    def test_from_rate_unicode_decimal_digits(self) -> None:
        """RateLimit.from_rate accepts non-ASCII decimal digits that int() parses."""
        rate = RateLimit.from_rate("\u0663/hour")
        assert rate.requests == 3

    def test_from_rate_zero_requests(self) -> None:
        """RateLimit.from_rate rejects zero request count."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_REQUESTS_NOT_POSITIVE),
        ) as exc_info:
            RateLimit.from_rate("0/hour")
        assert exc_info.value.context.get("requests") == 0

    def test_direct_construction_negative_requests(self) -> None:
        """RateLimit rejects negative request count."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_REQUESTS_NOT_POSITIVE),
        ) as exc_info:
            RateLimit(requests=-1, period=Period.HOUR)
        assert exc_info.value.context.get("requests") == -1

    def test_direct_construction_zero_requests(self) -> None:
        """RateLimit rejects zero request count."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_REQUESTS_NOT_POSITIVE),
        ) as exc_info:
            RateLimit(requests=0, period=Period.HOUR)
        assert exc_info.value.context.get("requests") == 0

    def test_period_seconds_for_second(self) -> None:
        """RateLimit.period_seconds returns 1 for SECOND."""
        rate = RateLimit(requests=5, period=Period.SECOND)
        assert rate.period_seconds == const.SECONDS_PER_SECOND

    def test_period_seconds_for_minute(self) -> None:
        """RateLimit.period_seconds returns 60 for MINUTE."""
        rate = RateLimit(requests=60, period=Period.MINUTE)
        assert rate.period_seconds == const.SECONDS_PER_MINUTE

    def test_period_seconds_for_hour(self) -> None:
        """RateLimit.period_seconds returns 3600 for HOUR."""
        rate = RateLimit(requests=100, period=Period.HOUR)
        assert rate.period_seconds == const.SECONDS_PER_HOUR

    def test_period_seconds_for_day(self) -> None:
        """RateLimit.period_seconds returns 86400 for DAY."""
        rate = RateLimit(requests=1000, period=Period.DAY)
        assert rate.period_seconds == const.SECONDS_PER_DAY

    def test_as_rate_roundtrip_hour(self) -> None:
        """RateLimit.as_rate serializes back to N/period form."""
        original = "100/hour"
        rate = RateLimit.from_rate(original)
        assert rate.as_rate() == original

    def test_as_rate_roundtrip_day(self) -> None:
        """RateLimit.as_rate roundtrips 10000/day."""
        original = "10000/day"
        rate = RateLimit.from_rate(original)
        assert rate.as_rate() == original

    def test_as_rate_roundtrip_second(self) -> None:
        """RateLimit.as_rate roundtrips 1/second."""
        original = "1/second"
        rate = RateLimit.from_rate(original)
        assert rate.as_rate() == original

    def test_as_rate_roundtrip_minute(self) -> None:
        """RateLimit.as_rate roundtrips 60/minute."""
        original = "60/minute"
        rate = RateLimit.from_rate(original)
        assert rate.as_rate() == original

    def test_frozen_prevents_modification(self) -> None:
        """RateLimit is frozen and prevents attribute modification."""
        rate = RateLimit(requests=100, period=Period.HOUR)
        with pytest.raises(FrozenInstanceError):
            rate.requests = 200  # type: ignore


class TestTierRate:
    """TierRate is a per-tier rate override."""

    def test_valid_tier_rate_creation(self) -> None:
        """TierRate accepts tier label and rate."""
        rate = RateLimit(requests=500, period=Period.HOUR)
        tier_rate = TierRate(tier="premium", rate=rate)
        assert tier_rate.tier == "premium"
        assert tier_rate.rate == rate

    def test_empty_tier_label_rejected(self) -> None:
        """TierRate rejects empty tier label."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_EMPTY_TIER),
        ):
            TierRate(tier="", rate=RateLimit(requests=500, period=Period.HOUR))

    def test_tier_rate_frozen(self) -> None:
        """TierRate is frozen and prevents modification."""
        tier_rate = TierRate(
            tier="premium", rate=RateLimit(requests=500, period=Period.HOUR)
        )
        with pytest.raises(FrozenInstanceError):
            tier_rate.tier = "enterprise"  # type: ignore


class TestThrottlePolicy:
    """ThrottlePolicy is a complete throttle declaration."""

    def test_valid_policy_with_base_rate_only(self) -> None:
        """ThrottlePolicy accepts scope and base rate."""
        rate = RateLimit(requests=100, period=Period.HOUR)
        policy = ThrottlePolicy(scope="api.users.list", rate=rate)
        assert policy.scope == "api.users.list"
        assert policy.rate == rate
        assert policy.tier_rates == ()

    def test_valid_policy_with_tier_overrides(self) -> None:
        """ThrottlePolicy accepts scope, rate, and tier overrides."""
        base_rate = RateLimit(requests=10, period=Period.HOUR)
        premium_tier = TierRate(
            tier="premium", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        policy = ThrottlePolicy(
            scope="api.data.export",
            rate=base_rate,
            tier_rates=(premium_tier,),
        )
        assert policy.scope == "api.data.export"
        assert policy.rate == base_rate
        assert len(policy.tier_rates) == 1

    def test_empty_scope_rejected(self) -> None:
        """ThrottlePolicy rejects empty scope."""
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_EMPTY_SCOPE),
        ):
            ThrottlePolicy(scope="", rate=RateLimit(requests=100, period=Period.HOUR))

    def test_duplicate_tier_labels_rejected(self) -> None:
        """ThrottlePolicy rejects duplicate tier labels."""
        base_rate = RateLimit(requests=10, period=Period.HOUR)
        tier1 = TierRate(
            tier="premium", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        tier2 = TierRate(
            tier="premium", rate=RateLimit(requests=200, period=Period.HOUR)
        )
        with pytest.raises(
            ThrottleDeclarationError,
            match=re.escape(const.ERR_POLICY_DUPLICATE_TIERS),
        ) as exc_info:
            ThrottlePolicy(
                scope="api.test",
                rate=base_rate,
                tier_rates=(tier1, tier2),
            )
        assert exc_info.value.context.get("scope") == "api.test"

    def test_has_tiers_false_when_empty(self) -> None:
        """ThrottlePolicy.has_tiers returns False with no tier overrides."""
        policy = ThrottlePolicy(
            scope="api.users.list",
            rate=RateLimit(requests=100, period=Period.HOUR),
        )
        assert policy.has_tiers is False

    def test_has_tiers_true_when_populated(self) -> None:
        """ThrottlePolicy.has_tiers returns True with tier overrides."""
        policy = ThrottlePolicy(
            scope="api.data.export",
            rate=RateLimit(requests=10, period=Period.HOUR),
            tier_rates=(
                TierRate(
                    tier="premium", rate=RateLimit(requests=100, period=Period.HOUR)
                ),
            ),
        )
        assert policy.has_tiers is True

    def test_rate_for_returns_override_when_declared(self) -> None:
        """ThrottlePolicy.rate_for returns tier override when declared."""
        base_rate = RateLimit(requests=10, period=Period.HOUR)
        premium_rate = RateLimit(requests=100, period=Period.HOUR)
        premium_tier = TierRate(tier="premium", rate=premium_rate)
        policy = ThrottlePolicy(
            scope="api.data.export",
            rate=base_rate,
            tier_rates=(premium_tier,),
        )
        result = policy.rate_for("premium")
        assert result == premium_rate

    def test_rate_for_returns_base_when_tier_not_declared(self) -> None:
        """ThrottlePolicy.rate_for returns base rate when tier not found."""
        base_rate = RateLimit(requests=10, period=Period.HOUR)
        premium_tier = TierRate(
            tier="premium", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        policy = ThrottlePolicy(
            scope="api.data.export",
            rate=base_rate,
            tier_rates=(premium_tier,),
        )
        result = policy.rate_for("enterprise")
        assert result == base_rate

    def test_rate_for_multiple_tiers(self) -> None:
        """ThrottlePolicy.rate_for correctly returns the requested tier."""
        base_rate = RateLimit(requests=10, period=Period.HOUR)
        premium_rate = RateLimit(requests=100, period=Period.HOUR)
        enterprise_rate = RateLimit(requests=1000, period=Period.HOUR)
        policy = ThrottlePolicy(
            scope="api.data.export",
            rate=base_rate,
            tier_rates=(
                TierRate(tier="premium", rate=premium_rate),
                TierRate(tier="enterprise", rate=enterprise_rate),
            ),
        )
        assert policy.rate_for("premium") == premium_rate
        assert policy.rate_for("enterprise") == enterprise_rate
        assert policy.rate_for("standard") == base_rate

    def test_throttle_policy_frozen(self) -> None:
        """ThrottlePolicy is frozen and prevents modification."""
        policy = ThrottlePolicy(
            scope="api.test",
            rate=RateLimit(requests=100, period=Period.HOUR),
        )
        with pytest.raises(FrozenInstanceError):
            policy.scope = "api.other"  # type: ignore
