"""Throttle policy constants. Imported as const."""

from __future__ import annotations

from typing import Final

THROTTLE_POLICY_ATTR: Final = "__throttle_policy__"

ERR_POLICY_REQUESTS_NOT_POSITIVE: Final = "rate requests must be positive"
ERR_POLICY_RATE_FORMAT: Final = "rate must use the N/period form"
ERR_POLICY_UNKNOWN_PERIOD: Final = "unknown rate period"
ERR_POLICY_EMPTY_TIER: Final = "tier label must be non-empty"
ERR_POLICY_EMPTY_SCOPE: Final = "scope must be non-empty"
ERR_POLICY_DUPLICATE_TIERS: Final = "tier labels must be unique"
ERR_POLICY_NO_PUBLIC_METHODS: Final = "class has no public methods to decorate"


"""Period length in seconds for throttle-rate calculations."""

SECONDS_PER_SECOND: Final = 1
SECONDS_PER_MINUTE: Final = 60
SECONDS_PER_HOUR: Final = 3600
SECONDS_PER_DAY: Final = 86400
