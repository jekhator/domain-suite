# domain-api-limiter Package Architecture

## Domain Boundaries

```
Rate-Limit Declaration Layer
=========================================================================

Principle: this package DECLARES throttle policy; it never enforces.
Enforcement belongs to the consuming framework's vetted throttling
(for example DRF throttle classes built from collected policies).

+----------------------+   +----------------------+   +---------------------+
| services/            |   | decorators/          |   | errors/             |
| policy/              |   | throttled/           |   | api_limiter_errors  |
|                      |   |                      |   |                     |
| Period (StrEnum)     |<--| @throttled(scope,    |   | ThrottleError       |
| RateLimit            |   |   rate, tiers=None)  |-->| |- RateLimitExceeded|
| TierRate             |   |                      |   | `- ThrottleDeclara- |
| ThrottlePolicy       |   | declaration-only:    |   |    tionError        |
|                      |   | validates, attaches  |   |                     |
| PolicyRegistry:      |   | policy metadata,     |   | [subclass DomainEr- |
| policy_of()          |   | returns func         |   |  ror, domain-errors]|
| collect()            |   | UNCHANGED            |   |                     |
`----------------------+   `----------------------+   `---------------------+
          ^
          | consuming framework adapter (not in this package)
          | walks collect() output and builds its own throttle classes

Aspects deliberately out of scope:
  - Enforcement, counters, storage backends: consuming framework only
  - HTTP integration: consumer adapters
  - Composability contract: the decorator is declaration-only (returns the
    function unchanged) so aggregate decorators can apply it mechanically
```

## Designed Surface

```
domain_api_limiter/services/policy/policy_objects.py
======================================================================
  Imports: from __future__ import annotations
           from dataclasses import dataclass
           from enum import StrEnum
           from typing import Self

----------------------------------------------------------------------
[ENUM]    Period(StrEnum)                   mirrors DRF rate vocabulary
----------------------------------------------------------------------
  |- SECOND = "second"
  |- MINUTE = "minute"
  |- HOUR   = "hour"
  `- DAY    = "day"

----------------------------------------------------------------------
[FROZEN]  RateLimit                          parsed "N/period" rate
----------------------------------------------------------------------
  |- requests : int          (must be positive)
  |- period   : Period
  |
  |- [vld] __post_init__(self) -> None            <- requests > 0
  |- [fct] from_rate(cls, rate: str) -> Self      <- parses "100/hour"
  |- [prp] period_seconds -> int                  <- 1 / 60 / 3600 / 86400
  `- [mth] as_rate(self) -> str                   <- "100/hour" round-trip

----------------------------------------------------------------------
[FROZEN]  TierRate                           per-tier rate override
----------------------------------------------------------------------
  |- tier : str              (consumer-defined label, non-empty)
  |- rate : RateLimit
  |
  `- [vld] __post_init__(self) -> None            <- tier non-empty

----------------------------------------------------------------------
[FROZEN]  ThrottlePolicy                     the declaration payload
----------------------------------------------------------------------
  |- scope      : str                            (non-empty)
  |- rate       : RateLimit                      (base rate)
  |- tier_rates : tuple[TierRate, ...] = ()      (unique tiers)
  |
  |- [vld] __post_init__(self) -> None            <- scope non-empty, tiers unique
  |- [prp] has_tiers -> bool
  `- [mth] rate_for(self, tier: str) -> RateLimit <- tier override or base rate

domain_api_limiter/services/policy/policy_client.py
======================================================================
----------------------------------------------------------------------
[SERVICE] PolicyRegistry                     introspection surface
----------------------------------------------------------------------
  |- [mth] policy_of(self, target) -> ThrottlePolicy | None
  |           <- reads the attached declaration attribute
  `- [mth] collect(self, container) -> tuple[ThrottlePolicy, ...]
              <- walks a class or module's callables for declarations
                (adapter consumption surface, declaration order preserved)

domain_api_limiter/decorators/throttled/throttled_client.py
======================================================================
----------------------------------------------------------------------
[SERVICE] Throttled                          declaration decorator factory
----------------------------------------------------------------------
  |- [mth] __call__(self, scope, rate, tiers=None)
  |           -> Callable[[Decorated], Decorated]
  |           <- validates + builds ThrottlePolicy at decoration
  |             (bad declarations raise ThrottleDeclarationError at import)
  |           <- attaches policy metadata; returns the function UNCHANGED
  `- Module handle: throttled = Throttled()

domain_api_limiter/errors/api_limiter_errors.py
======================================================================
  ThrottleError(DomainError)          domain="api_limiter" | 429 | retryable
  |- RateLimitExceeded                code=rate_limit_exceeded | 429
  |     (consumer-side mapping type for framework throttle responses)
  `- ThrottleDeclarationError         code=throttle_declaration_invalid | 500
        (declaration-time failure; not retryable)
```

## Public API (domain_api_limiter/__init__.py)

Re-exports: `Period`, `RateLimit`, `TierRate`, `ThrottlePolicy`, `PolicyRegistry`, `throttled`, `ThrottleError`, `RateLimitExceeded`, `ThrottleDeclarationError`, `__version__`. The `Throttled` class stays feature-level (mirror of the domain-security scoping ruling).
