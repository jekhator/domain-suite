# domain_aspects: Flow-Trace

## Overview

Cross-cutting aspect composition service for stacking decorators in a fixed order. Entry types (`Logged`, `Requires`, `TenantScoped`, `Throttled`, `Monitored`, `WrapErrors`, `Retried`, `RequireMixins`) are frozen value objects. Each one lazily imports its underlying decorator inside `build()` and applies it. Composition validates duplicate kinds and empty declarations, then applies entries innermost-first (reverse of `ASPECT_ORDER`).

## Entry Unit

`aspects(...)` calls `Aspects.__call__(*entries)`, which returns a decorator factory.

## Flow-Trace

```
(1) CONSTRUCT entries [frozen, slots]
    Logged(event="fetch.user")                     needs mixin-logging
    Requires(permission="data:read")               needs domain-security
    TenantScoped(param_name="tenant_id")           needs domain-security
    Throttled(scope="api:fetch", rate="100/hour")  needs domain-api-limiter
    Monitored(event="fetch")                       needs domain-monitoring
    WrapErrors(as_=ValidationError)                needs domain-errors
    Retried(policy=RetryPolicy(...))               needs mixin-retry
    RequireMixins(bases=(MixinA,))                 validation only

    AspectKind: StrEnum, one value per entry type

(2) COMPOSE aspects(...)
    Aspects.__call__(*entries)
      |- _flatten(entries)        frozensets and single entries become one list
      |- _validate(flattened)
      |    |- empty            -> AspectDeclarationError(ERR_ASPECTS_EMPTY_DECLARATION)
      |    |- unknown type     -> AspectDeclarationError(ERR_ASPECTS_UNKNOWN_ENTRY_TYPE)
      |    |- duplicate kind   -> AspectDeclarationError(ERR_ASPECTS_DUPLICATE_KIND)
      |- _sort(flattened)          by ASPECT_ORDER; unknown kinds sort last
      `- returns decorator(target)

(3) DECORATE (innermost first)
    result = target
    for entry in reversed(sorted_entries):
        result = entry.build()(result)
    return result

    Wrapping order, innermost to outermost:
      RETRIED         RetryExecutor wrapper; sees raw exceptions
      WRAP_ERRORS     @wrap_errors(as_=..., catch=...)
      MONITORED       @monitored(event=..., sink=...)
      THROTTLED       @throttled(scope=..., rate=..., tiers=...)
      TENANT_SCOPED   @tenant_scoped(param_name=...)
      REQUIRES        @requires(permission=...)
      LOGGED          start/end/error events, outermost

    Class targets: LOGGED, RETRIED and the security decorators fan out over
    public methods declared on the class. RequireMixins checks bases only.

(4) RUNTIME CALL, outermost layer first
    LOGGED        emit <event>.start
    REQUIRES      permission check; AuthzError stops the call before MONITORED
    TENANT_SCOPED tenant check; TenancyError stops the call
    THROTTLED     quota check
    MONITORED     time the call; emit success or failure metric
    WRAP_ERRORS   DomainError passes through; other listed exceptions are wrapped
    RETRIED       retries the call per policy
    LOGGED        emit <event>.end, or <event>.error and re-raise
```

## Key Constants

- `ASPECT_ORDER` = ("LOGGED", "REQUIRES", "TENANT_SCOPED", "THROTTLED", "MONITORED", "WRAP_ERRORS", "RETRIED")
- `LOGGED_APPLIED_MARKER` = "__logged_applied__"
- `RETRIED_APPLIED_MARKER` = "__retried_applied__"
- `ERR_ASPECTS_EMPTY_DECLARATION` = "Aspect declaration is empty."
- `ERR_ASPECTS_DUPLICATE_KIND` = "Duplicate aspect kind in declaration: {kind}."
- `ERR_ASPECTS_UNKNOWN_ENTRY_TYPE` = "Unknown aspect entry type: {entry_type}."

## Core Classes

- `AspectKind`: StrEnum with LOGGED, REQUIRES, TENANT_SCOPED, THROTTLED, MONITORED, WRAP_ERRORS, RETRIED, REQUIRE_MIXINS
- `Logged`: frozen slots; event, payload extractors, timed; build() returns a logged wrapper
- `Requires`: frozen slots; permission; build() returns the requires decorator
- `TenantScoped`: frozen slots; param_name (default "tenant_id"); build() returns the tenant_scoped decorator
- `Throttled`: frozen slots; scope, rate, tiers; build() returns the throttled decorator
- `Monitored`: frozen slots; event, sink, label callbacks; build() returns the monitored decorator
- `WrapErrors`: frozen slots; as_, catch (default (Exception,)); build() returns the wrap_errors decorator
- `Retried`: frozen slots; policy or policy_from_request; build() returns a retry decorator
- `RequireMixins`: frozen slots; bases; build() returns a validation-only decorator
- `AspectEntry`: union type alias of the entry types
- `Aspects`: __call__, _flatten, _validate, _sort
