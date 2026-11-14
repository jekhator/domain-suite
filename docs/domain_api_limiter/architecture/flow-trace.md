# domain_api_limiter: Flow-Trace

## Overview

Declarative rate-limit policy attachment via `@throttled` decorator. Policies are frozen value objects parsed from rate strings (e.g., "100/hour"). Class-level decoration fans policy across public methods, auto-scoped as "{root}:{method_name}". Policy introspection is read-only; actual rate enforcement happens downstream (integration layer).

## Entry Unit

`@throttled(scope, rate, tiers)` decorator --> `ThrottlePolicy` [FROZEN,slots].

## Flow-Trace Diagram

```
1. CONSTRUCT Rate Policy
   RateLimit.from_rate("100/hour")  <- parse N/period string
      |- head, separator, tail = rate.partition("/")  <- "100", "/", "hour"
      |- head.isdigit() and separator?  --> continue | raise ThrottleDeclarationError
      |- period = Period(tail)  <- StrEnum.SECOND/MINUTE/HOUR/DAY
      `- return RateLimit(requests=100, period=Period.HOUR)

   Period.HOUR  --> period_seconds: 3600 (SECONDS_PER_HOUR constant)
   Period.MINUTE  --> period_seconds: 60
   Period.SECOND  --> period_seconds: 1
   Period.DAY  --> period_seconds: 86400

   ThrottlePolicy(scope="api:documents", rate=RateLimit(...), tier_rates=())
      `- __post_init__: validate scope non-empty, tier labels unique

2. DECORATE @throttled
   @throttled(scope="api:documents", rate="100/hour")  --> Throttled.__call__()
      |- policy = ThrottlePolicy(...)  <- validated rate parsed
      |- declare(target)
      |  |- isclass(target)?
      |  |  |- YES --> _decorate_class(target, root_policy)
      |  |  |  |- _select_public_methods(cls)  <- skip _-prefixed, dunders, properties, nested classes
      |  |  |  |- for method_name, method_obj in public_methods
      |  |  |  |  |- hasattr(method_obj, "__throttle_policy__")?  --> skip already decorated
      |  |  |  |  |- method_scope = "{root_policy.scope}:{method_name}"  <- fan-out scope
      |  |  |  |  |- method_policy = ThrottlePolicy(scope=method_scope, rate=root_policy.rate, tier_rates=root_policy.tier_rates)
      |  |  |  |  `- setattr(method_obj, "__throttle_policy__", method_policy)
      |  |  |  `- returns cls
      |  |  `- NO (callable) --> setattr(target, "__throttle_policy__", policy)
      `- returns target (unchanged callable, modified class)

3. INTROSPECTION (read-only)
   PolicyRegistry().policy_of(callable)  <- getattr(callable, "__throttle_policy__", None)
      `- returns ThrottlePolicy | None

   PolicyRegistry().collect(class_or_module)  <- introspect all members
      `- returns tuple[ThrottlePolicy, ...]

4. POLICY ATTACHED (decorator marker)
   hasattr(list_documents, "__throttle_policy__")  <- setattr by decorator
      `- policy = ThrottlePolicy(scope="api:documents", rate=RateLimit(requests=100, period=Period.HOUR), tier_rates=())

REAL OUTPUT (introspection):
   POLICY ATTACHED: api:documents
     rate: 100/hour
     period_seconds: 3600
     has_tiers: False
     rate.as_rate(): 100/hour
   RESULT: [{'id': '1', 'name': 'doc.pdf'}]
```

## Key Constants

- `THROTTLE_POLICY_ATTR` = "__throttle_policy__" <- marker attribute on decorated callable
- `SECONDS_PER_SECOND` = 1
- `SECONDS_PER_MINUTE` = 60
- `SECONDS_PER_HOUR` = 3600
- `SECONDS_PER_DAY` = 86400
- `ERR_POLICY_REQUESTS_NOT_POSITIVE` = "rate requests must be positive"
- `ERR_POLICY_RATE_FORMAT` = "rate must use the N/period form"
- `ERR_POLICY_UNKNOWN_PERIOD` = "unknown rate period"
- `ERR_POLICY_EMPTY_TIER` = "tier label must be non-empty"
- `ERR_POLICY_EMPTY_SCOPE` = "scope must be non-empty"
- `ERR_POLICY_DUPLICATE_TIERS` = "tier labels must be unique"
- `ERR_POLICY_NO_PUBLIC_METHODS` = "class has no public methods to decorate"

## Core Classes

- `RateLimit` <- frozen slots; requests (int), period (Period enum); from_rate(str) classmethod; period_seconds property
- `Period` <- StrEnum; SECOND, MINUTE, HOUR, DAY
- `TierRate` <- frozen slots; tier (str), rate (RateLimit)
- `ThrottlePolicy` <- frozen slots; scope (str), rate (RateLimit), tier_rates (tuple); has_tiers property; rate_for(tier) method
- `Throttled` <- decorator factory; __call__(scope, rate, tiers); _decorate_class, _select_public_methods, _tier_rates
- `PolicyRegistry` <- read-only introspection; policy_of(target) -> ThrottlePolicy | None; collect(container) -> tuple[ThrottlePolicy, ...]
- `ThrottleDeclarationError` <- DomainError subclass; message + context (class_name, requests, rate, period, scope)

## Note

Policy enforcement (actual rate-limit checking) is NOT in this package; the decorator is declaration-only. Integration layer (e.g., Django middleware, FastAPI dependency) reads policies via `PolicyRegistry` and performs Redis/token-bucket checks at runtime.
