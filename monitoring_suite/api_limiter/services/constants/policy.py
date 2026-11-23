"""Throttle policy constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Attribute the decorator stores the resolved policy under."""

THROTTLE_POLICY_ATTR: Final[str] = "__throttle_policy__"


"""Throttle policy validation error messages."""

ERR_POLICY_REQUESTS_NOT_POSITIVE: Final[str] = "rate requests must be positive"
ERR_POLICY_RATE_FORMAT: Final[str] = "rate must use the N/period form"
ERR_POLICY_UNKNOWN_PERIOD: Final[str] = "unknown rate period"
ERR_POLICY_EMPTY_TIER: Final[str] = "tier label must be non-empty"
ERR_POLICY_EMPTY_SCOPE: Final[str] = "scope must be non-empty"
ERR_POLICY_DUPLICATE_TIERS: Final[str] = "tier labels must be unique"
ERR_POLICY_NO_PUBLIC_METHODS: Final[str] = "class has no public methods to decorate"


"""Period length in seconds for throttle-rate calculations."""

SECONDS_PER_SECOND: Final[int] = 1
SECONDS_PER_MINUTE: Final[int] = 60
SECONDS_PER_HOUR: Final[int] = 3600
SECONDS_PER_DAY: Final[int] = 86400


"""Separators and format pieces."""

SCOPE_SEPARATOR: Final[str] = ":"
RATE_SEPARATOR: Final[str] = "/"


"""Decorator markers and member-name conventions."""

PRIVATE_PREFIX: Final[str] = "_"


"""Enumeration member values."""

PERIOD_SECOND: Final[str] = "second"
PERIOD_MINUTE: Final[str] = "minute"
PERIOD_HOUR: Final[str] = "hour"
PERIOD_DAY: Final[str] = "day"
