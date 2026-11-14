# Throttle Policy Objects

## Purpose

`ThrottlePolicy`, `RateLimit`, `TierRate`, and `Period` are immutable value objects that define rate-limit policies. They validate constraints at creation time so invalid policies fail fast at import, before any code runs. Policies carry only scope names, rates, and tier labels: no secrets, no personal data.

## Behavior

### Period

`Period` is a string enumeration defining standard rate periods.

```python
from domain_api_limiter import Period

Period.SECOND  # "second" (1 second)
Period.MINUTE  # "minute" (60 seconds)
Period.HOUR    # "hour" (3600 seconds)
Period.DAY     # "day" (86400 seconds)
```

Periods are ordered by duration and mirror common framework rate-limiting vocabularies (Django REST Framework, etc.).

### RateLimit

`RateLimit` represents a count of requests per period. It validates that requests are positive and supports parsing from "N/period" rate strings.

```python
from domain_api_limiter import RateLimit, Period

# Direct creation
rate = RateLimit(requests=100, period=Period.HOUR)

# Parsing from rate strings
rate = RateLimit.from_rate("100/hour")

# Properties
rate.requests        # 100
rate.period          # Period.HOUR
rate.period_seconds  # 3600
rate.as_rate()       # "100/hour"
```

Parsing accepts the format "N/period" where N is a positive integer and period is one of second, minute, hour, day. Invalid formats, non-positive counts, or unknown periods raise `ThrottleDeclarationError` at parse time.

### TierRate

`TierRate` associates a tier label with a rate override. Tier labels must be non-empty strings (e.g., "free", "pro", "enterprise").

```python
from domain_api_limiter import TierRate, RateLimit

tier_rate = TierRate(
    tier="free",
    rate=RateLimit.from_rate("10/day")
)
```

Empty tier labels raise `ThrottleDeclarationError`.

### ThrottlePolicy

`ThrottlePolicy` combines a scope identifier, a base rate, and optional tier overrides. It validates that scopes are non-empty and tier labels are unique.

```python
from domain_api_limiter import ThrottlePolicy, RateLimit, TierRate

policy = ThrottlePolicy(
    scope="docs:list",
    rate=RateLimit.from_rate("100/hour"),
    tier_rates=(
        TierRate("free", RateLimit.from_rate("10/day")),
        TierRate("pro", RateLimit.from_rate("1000/hour")),
    )
)

# Inspect the policy
policy.scope          # "docs:list"
policy.rate           # RateLimit(requests=100, period=Period.HOUR)
policy.has_tiers      # True
policy.tier_rates     # (TierRate(...), TierRate(...))

# Resolve rate by tier
policy.rate_for("free")     # RateLimit for "free" tier
policy.rate_for("pro")      # RateLimit for "pro" tier
policy.rate_for("unknown")  # Base rate (no override found)
```

Empty scopes or duplicate tier labels raise `ThrottleDeclarationError`.

## Public Surface

### Period

```python
class Period(StrEnum):
    SECOND: str
    MINUTE: str
    HOUR: str
    DAY: str
```

### RateLimit

```python
@dataclass(frozen=True, slots=True)
class RateLimit:
    requests: int
    period: Period

    @classmethod
    def from_rate(cls, rate: str) -> Self:
        """Parse an N/period rate string into a RateLimit."""

    @property
    def period_seconds(self) -> int:
        """Return the period length in seconds."""

    def as_rate(self) -> str:
        """Serialize back to the N/period form."""
```

### TierRate

```python
@dataclass(frozen=True, slots=True)
class TierRate:
    tier: str
    rate: RateLimit
```

### ThrottlePolicy

```python
@dataclass(frozen=True, slots=True)
class ThrottlePolicy:
    scope: str
    rate: RateLimit
    tier_rates: tuple[TierRate, ...] = ()

    @property
    def has_tiers(self) -> bool:
        """Return True when tier overrides are declared."""

    def rate_for(self, tier: str) -> RateLimit:
        """Return the tier override when declared, otherwise the base rate."""
```

## Constants

### From `domain_api_limiter.services.constants.policy`

```python
THROTTLE_POLICY_ATTR: Final = "__throttle_policy__"
```

The attribute name that the `@throttled` decorator attaches to callables. Used internally by `PolicyRegistry.policy_of()` to retrieve policies.

## Error Semantics

Validation errors are raised at object creation time, ensuring policies are valid before any request handling:

- `ThrottleDeclarationError` with message "rate requests must be positive" when `RateLimit.requests <= 0`.
- `ThrottleDeclarationError` with message "rate must use the N/period form" when parsing a malformed rate string.
- `ThrottleDeclarationError` with message "unknown rate period" when the period part of a rate string is not one of second/minute/hour/day.
- `ThrottleDeclarationError` with message "tier label must be non-empty" when `TierRate.tier` is empty.
- `ThrottleDeclarationError` with message "scope must be non-empty" when `ThrottlePolicy.scope` is empty.
- `ThrottleDeclarationError` with message "tier labels must be unique" when `ThrottlePolicy.tier_rates` contains duplicate tier labels.

## Example Usage

### Basic Rate Creation

```python
from domain_api_limiter import RateLimit, Period

# Create and inspect a rate
rate = RateLimit(requests=100, period=Period.HOUR)
print(rate.period_seconds)  # 3600
print(rate.as_rate())        # "100/hour"

# Parse from a string
rate = RateLimit.from_rate("20/minute")
print(rate.requests)  # 20
```

### Policy with Tier Overrides

```python
from domain_api_limiter import ThrottlePolicy, RateLimit, TierRate

policy = ThrottlePolicy(
    scope="api:call",
    rate=RateLimit.from_rate("100/hour"),
    tier_rates=(
        TierRate("free", RateLimit.from_rate("10/hour")),
        TierRate("pro", RateLimit.from_rate("1000/hour")),
        TierRate("enterprise", RateLimit.from_rate("unlimited")),  # Hypothetical
    )
)

# Resolve rates
base = policy.rate_for("unknown")  # RateLimit(100, HOUR)
free = policy.rate_for("free")     # RateLimit(10, HOUR)
pro = policy.rate_for("pro")       # RateLimit(1000, HOUR)
```

### Validation

```python
from domain_api_limiter import ThrottleDeclarationError, RateLimit

# Non-positive request count
try:
    RateLimit(requests=0, period="hour")
except ThrottleDeclarationError as e:
    print(e.message)  # "rate requests must be positive"

# Malformed rate string
try:
    RateLimit.from_rate("notarate")
except ThrottleDeclarationError as e:
    print(e.message)  # "rate must use the N/period form"

# Unknown period
try:
    RateLimit.from_rate("100/century")
except ThrottleDeclarationError as e:
    print(e.message)  # "unknown rate period"
```

## See Also

- [Throttled Decorator](throttled.md) for attaching policies to methods.
- [Policy Registry](throttled.md#policy-registry) for collecting policies from service classes.
- [Error Types](api_limiter_errors.md) for error handling.
