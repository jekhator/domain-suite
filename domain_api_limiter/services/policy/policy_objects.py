"""Throttle policy value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from domain_api_limiter.errors.api_limiter_errors import ThrottleDeclarationError
from domain_api_limiter.services.constants import policy as const


class Period(StrEnum):
    """Rate period vocabulary, mirroring framework rate strings."""

    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass(frozen=True, slots=True)
class RateLimit:
    """Parsed rate: allowed request count per period."""

    requests: int
    period: Period

    def __post_init__(self) -> None:
        """Reject non-positive request counts."""
        if self.requests <= 0:
            raise ThrottleDeclarationError(
                message=const.ERR_POLICY_REQUESTS_NOT_POSITIVE,
                requests=self.requests,
            )

    @classmethod
    def from_rate(cls, rate: str) -> Self:
        """Parse an N/period rate string into a RateLimit."""
        head, separator, tail = rate.partition("/")
        if not separator or not head.isdecimal():
            raise ThrottleDeclarationError(
                message=const.ERR_POLICY_RATE_FORMAT,
                rate=rate,
            )
        try:
            period = Period(tail)
        except ValueError as error:
            raise ThrottleDeclarationError(
                message=const.ERR_POLICY_UNKNOWN_PERIOD,
                rate=rate,
                period=tail,
            ) from error
        return cls(requests=int(head), period=period)

    @property
    def period_seconds(self) -> int:
        """Return the period length in seconds."""
        match self.period:
            case Period.SECOND:
                return const.SECONDS_PER_SECOND
            case Period.MINUTE:
                return const.SECONDS_PER_MINUTE
            case Period.HOUR:
                return const.SECONDS_PER_HOUR
            case Period.DAY:
                return const.SECONDS_PER_DAY

    def as_rate(self) -> str:
        """Serialize back to the N/period form."""
        return f"{self.requests}/{self.period.value}"


@dataclass(frozen=True, slots=True)
class TierRate:
    """Per-tier rate override keyed by a consumer-defined tier label."""

    tier: str
    rate: RateLimit

    def __post_init__(self) -> None:
        """Reject empty tier labels."""
        if not self.tier:
            raise ThrottleDeclarationError(message=const.ERR_POLICY_EMPTY_TIER)


@dataclass(frozen=True, slots=True)
class ThrottlePolicy:
    """Complete throttle declaration: scope, base rate, and tier overrides."""

    scope: str
    rate: RateLimit
    tier_rates: tuple[TierRate, ...] = ()

    def __post_init__(self) -> None:
        """Reject empty scopes and duplicate tier labels."""
        if not self.scope:
            raise ThrottleDeclarationError(message=const.ERR_POLICY_EMPTY_SCOPE)
        tiers = [tier_rate.tier for tier_rate in self.tier_rates]
        if len(tiers) != len(set(tiers)):
            raise ThrottleDeclarationError(
                message=const.ERR_POLICY_DUPLICATE_TIERS,
                scope=self.scope,
            )

    @property
    def has_tiers(self) -> bool:
        """Return True when tier overrides are declared."""
        return bool(self.tier_rates)

    def rate_for(self, tier: str) -> RateLimit:
        """Return the tier override when declared, otherwise the base rate."""
        for tier_rate in self.tier_rates:
            if tier_rate.tier == tier:
                return tier_rate.rate
        return self.rate
