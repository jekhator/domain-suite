# Aspects Service

Composable aspect decorators for stacking cross-cutting concerns.

## Overview

The Aspects service enables declarative composition of six cross-cutting aspects: logging, authorization, tenancy, throttling, error wrapping, and sensitive field masking.

Key design:

- **Immutable entries**: All aspect entries are frozen dataclasses with hashable fields for frozenset membership.
- **Lazy imports**: Optional dependencies (logging-suite, monitoring_suite.security, monitoring_suite.api_limiter, logging-suite) are imported only when an entry's `build()` method is called, so validation works without them installed.
- **Canonical ordering**: Aspects apply in ASPECT_ORDER regardless of declaration order (LOGGED outermost, WRAP_ERRORS innermost).
- **Validation at decoration time**: Duplicate kinds, unknown entry types, and empty declarations raise AspectDeclarationError.

## Entry Types

### Logged

```python
Logged(event: str)
```

Emit entry and exit events via logging-suite.

### Requires

```python
Requires(permission: str)
```

Check permissions against a security context via monitoring_suite.security.

### TenantScoped

```python
TenantScoped(param_name: str = "tenant_id")
```

Enforce tenant isolation via monitoring_suite.security.

### Throttled

```python
Throttled(scope: str, rate: str, tiers: tuple[tuple[str, str], ...] = ())
```

Apply rate limiting via monitoring_suite.api_limiter. Tiers are optional per-tier rate overrides.

### WrapErrors

```python
WrapErrors(as_: type, catch: tuple[type[BaseException], ...] = (Exception,))
```

Translate exceptions to a target exception type via monitoring_suite.errors.

## Usage

### Single Entry

```python
@aspects(Logged(event="service.method"))
def method(self) -> None:
    pass
```

### Frozenset

```python
@aspects(frozenset({
    Logged(event="service.method"),
    Requires(permission="admin.read"),
}))
def method(self) -> None:
    pass
```

### Mixed

```python
@aspects(
    Logged(event="service.method"),
    frozenset({Requires(permission="admin.read")}),
    WrapErrors(as_=ValueError),
)
def method(self) -> None:
    pass
```

## Error Handling

Declaration-time validation raises AspectDeclarationError when:

- Duplicate aspect kinds (e.g., two Logged entries).
- Unknown entry type (not one of the six official types).
- Empty declaration (frozenset or argument list with no entries).

## Optional Dependencies

Each aspect has an optional extra for its underlying library:

<<<<<<< HEAD:docs/aspects/apps/aspects/aspects.md
- `[logging]` : logging-suite
- `[security]` : monitoring_suite.security
- `[throttle]` : monitoring_suite.api_limiter
- `[sensitivity]` : logging-suite
- `[all]` : all four
||||||| 4d36750:docs/aspects/apps/aspects/aspects.md
- `[logging]`: logging-suite
- `[security]`: monitoring_suite.security
- `[throttle]`: monitoring_suite.api_limiter
- `[sensitivity]`: logging-suite
- `[all]`: all four
=======
- `[logging]`: logging-suite
- `[security]`: monitoring_suite.security
- `[throttle]`: monitoring_suite.api_limiter
- `[sensitivity]`: logging-suite
- `[all]`: all four
>>>>>>> origin/main:docs/monitoring_suite/aspects/apps/aspects/aspects.md

Install with:

```bash
pip install monitoring_suite.aspects[all]
```

## Ordering

Aspects apply in this canonical order (outermost-to-innermost):

1. LOGGED (outermost: emits start/exit events)
2. REQUIRES (permission check)
3. TENANT_SCOPED (tenant boundary enforcement)
4. THROTTLED (rate limiting)
5. MONITORED (metric emission)
6. WRAP_ERRORS (exception translation)
7. RETRIED (innermost: retries see raw exceptions)

This order is enforced by the Aspects service during composition, regardless of the order you declare entries.
