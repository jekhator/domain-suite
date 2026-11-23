# monitoring_suite.aspects: Flow-Trace

## Overview

Cross-cutting aspect composition service for stacking decorators in canonical order. Entry types (`Logged`, `Requires`, `TenantScoped`, `Throttled`, `Monitored`, `WrapErrors`, `Retried`) are frozen value objects that lazily import their underlying decorators and apply them innermost-first (reverse sort by `ASPECT_ORDER`). Validates duplicate kinds and empty declarations.

## Entry Unit

`aspects(...)` ── `Aspects.__call__(*entries)` ──▶ factory decorator.

## Flow-Trace Diagram

```
① CONSTRUCT Aspect Entries [FROZEN,slots each]
   Logged(event="fetch.user")  ← from logging_suite.logging
   Requires(permission="data:read")  ← from monitoring_suite.security
   TenantScoped(param_name="tenant_id")  ← from monitoring_suite.security
   Throttled(scope="api:fetch", rate="100/hour", tiers=())  ← from monitoring_suite.api_limiter
   Monitored(event="fetch", sink=None)  ← from monitoring_suite.monitoring
   WrapErrors(as_=ValidationError, catch=(Exception,))  ← from monitoring_suite.errors

   AspectKind ← StrEnum: LOGGED, REQUIRES, TENANT_SCOPED, THROTTLED, MONITORED, WRAP_ERRORS, RETRIED, REQUIRE_MIXINS

② COMPOSE aspects(...)
   @aspects(
       Logged(...),
       Requires(...),
       Monitored(...),
       WrapErrors(...),
   )
   ──▶ Aspects.__call__(*entries)
      ├─ _flatten(entries)  ← handle frozenset[AspectEntry] and single entries
      ├─ _validate(flattened)
      │  ├─ if not entries  ──▶ raise AspectDeclarationError(ERR_ASPECTS_EMPTY_DECLARATION)
      │  ├─ for entry in entries
      │  │  ├─ isinstance(entry, (Logged, Requires, ...))  ← type check
      │  │  │  └─ if False  ──▶ raise AspectDeclarationError(ERR_ASPECTS_UNKNOWN_ENTRY_TYPE)
      │  │  ├─ kind = entry.kind  ← AspectKind enum value
      │  │  ├─ if kind in seen_kinds  ──▶ raise AspectDeclarationError(ERR_ASPECTS_DUPLICATE_KIND)
      │  │  └─ seen_kinds.add(kind)
      │  └─ validated
      ├─ _sort(flattened)  ← sort by ASPECT_ORDER
      │  ├─ order_map = {"LOGGED": 0, "REQUIRES": 1, ..., "WRAP_ERRORS": 6}
      │  └─ sorted(entries, key=lambda e: order_map.get(e.kind, 999))
      └─ returns decorator factory

③ DECORATE (decorator applies in reverse order = innermost-to-outermost)
   def decorator(target):
       result = target
       for entry in reversed(sorted_entries):  ← WRAP_ERRORS (6) -> ... -> LOGGED (0)
           decorator_fn = entry.build()  ← lazy import + instantiate
           result = decorator_fn(result)  ← wrap result
       return result

   WRAPPING ORDER (innermost to outermost):
   ├─ WRAP_ERRORS innermost  ← wraps original target
   │  └─ @wrap_errors(as_=ValidationError, catch=(Exception,))
   ├─ MONITORED
   │  └─ @monitored(event="...", sink=...)  ← MetricSink.emit() on success/failure
   ├─ THROTTLED
   │  └─ @throttled(scope="...", rate="...", tiers=...)  ← declarative, reads at middleware
   ├─ TENANT_SCOPED
   │  └─ @tenant_scoped(param_name="tenant_id")  ← from monitoring_suite.security
   ├─ REQUIRES
   │  └─ @requires(permission="...")  ← AuthzError if denied
   └─ LOGGED outermost  ← @logged(event="...")  ← from logging_suite.logging

④ RUNTIME CALL ──▶ decorated_function(...)
   Flow executes outer-to-inner (LOGGED outermost first):
   ├─ LOGGED layer
   │  └─ emit entry event
   ├─ REQUIRES layer
   │  └─ SecurityContextManager().get() ──▶ check permission ──▶ raise AuthzError | continue
   ├─ TENANT_SCOPED layer
   │  └─ extract tenant_id from args, bind SecurityContext(principal, tenant_id)
   ├─ THROTTLED layer
   │  └─ policy declared but not enforced here (middleware/integration checks at call time)
   ├─ MONITORED layer
   │  └─ start_time, try/except, emit MetricEvent.for_success/for_failure, raise on exception
   └─ WRAP_ERRORS innermost
      ├─ try: return original_function(...)
      ├─ except DomainError: raise (pass-through)
      └─ except (Exception, ...): raise classified error from original exception

   Returns: result | raises exception

⑤ EXAMPLE BUILD (per entry)
   Logged(event="export.run").build()
      └─ from logging_suite.logging import logged  ──▶ return logged(event)
   Requires(permission="data:export").build()
      └─ from monitoring_suite.security.decorators.requires import requires  ──▶ return requires(permission)
   WrapErrors(as_=ValidationError).build()
      └─ from monitoring_suite.errors import wrap_errors  ──▶ return wrap_errors(as_=ValidationError, catch=(Exception,))
   Monitored(event="export.run", sink=sink).build()
      └─ from monitoring_suite.monitoring.decorators.monitored import monitored  ──▶ return monitored(event, sink=sink)

REAL OUTPUT (composed call, anonymous):
   CAUGHT AuthzError (REQUIRES layer): AuthzError
   ← REQUIRES rejects before MONITORED emits (ordering by ASPECT_ORDER)

REAL OUTPUT (composed call, with permission):
   SUCCESS: export_completed
   MONITORED (MONITORED layer): export.run (outcome=success)
   ← MONITORED emits success event after WRAP_ERRORS catches/translates
```

## Key Constants

- `ASPECT_ORDER` = ("LOGGED", "REQUIRES", "TENANT_SCOPED", "THROTTLED", "MONITORED", "WRAP_ERRORS", "RETRIED")
  - applies in reverse: WRAP_ERRORS applied first (innermost), LOGGED applied last (outermost)
- `ERR_ASPECTS_EMPTY_DECLARATION` = "Aspect declaration is empty."
- `ERR_ASPECTS_DUPLICATE_KIND` = "Duplicate aspect kind in declaration: {kind}."
- `ERR_ASPECTS_UNKNOWN_ENTRY_TYPE` = "Unknown aspect entry type: {entry_type}."

## Core Classes

- `AspectKind` ← StrEnum; LOGGED, REQUIRES, TENANT_SCOPED, THROTTLED, MONITORED, WRAP_ERRORS, RETRIED, REQUIRE_MIXINS
- `Logged` ← frozen slots; event (str); kind property; build() -> logged decorator
- `Requires` ← frozen slots; permission (str); kind property; build() -> requires decorator
- `TenantScoped` ← frozen slots; param_name (str, default="tenant_id"); kind property; build() -> tenant_scoped decorator
- `Throttled` ← frozen slots; scope (str), rate (str), tiers (tuple of tuples); kind property; build() -> throttled decorator
- `Monitored` ← frozen slots; event (str), sink (MetricSink | None); kind property; build() -> monitored decorator
- `WrapErrors` ← frozen slots; as_ (exception class), catch (tuple[BaseException, ...], default=(Exception,)); kind property; build() -> wrap_errors decorator
- `AspectEntry` ← Union type alias for all entry types
- `Aspects` ← __call__(*entries), _flatten(), _validate(), _sort(); returns decorator factory

## Design Principles

1. **Canonical Ordering** ← ASPECT_ORDER determines nesting depth (innermost-to-outermost)
2. **Lazy Import** ← entry.build() imports underlying package on first composition (safe if optional)
3. **Validation** ← duplicate kinds rejected at decoration time, not runtime
4. **Immutable** ← all entries frozen; no side effects on composition
5. **Composable** ← entries can mix and match; frozenset[entry] flattens naturally
