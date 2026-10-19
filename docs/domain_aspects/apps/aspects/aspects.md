# Aspects Service

Composable aspect decorators for stacking cross-cutting concerns.

## Overview

The Aspects service enables declarative composition of cross-cutting aspects: logging, authorization, tenancy, throttling, metric emission, error wrapping, retries, and mixin validation.

Key design:

- **Immutable entries**: All aspect entries are frozen dataclasses with hashable fields for frozenset membership.
- **Lazy imports**: Optional dependencies (mixin-logging, domain-security, domain-api-limiter, domain-monitoring, domain-errors, mixin-retry) are imported only when an entry's `build()` method is called, so validation works without them installed.
- **Fixed ordering**: Aspects apply in `ASPECT_ORDER` regardless of declaration order (LOGGED outermost, RETRIED innermost).
- **Validation at decoration time**: Duplicate kinds, unknown entry types, and empty declarations raise `AspectDeclarationError`.

## Entry Types

### Logged

```python
Logged(
    event: str,
    payload_from_request=None,
    payload_from_result=None,
    payload_from_exc=None,
    timed: bool = False,
)
```

Emit `<event>.start`, `<event>.end` and `<event>.error` events via mixin-logging. When the target is a `LoggingMixin` instance, the instance logger is used; otherwise the ambient logging functions are used. Payload extractors that raise are logged and skipped. `timed=True` adds `latency_ms` to the end and error payloads.

### Requires

```python
Requires(permission: str)
```

Check permissions against a security context via domain-security.

### TenantScoped

```python
TenantScoped(param_name: str = "tenant_id")
```

Enforce tenant isolation via domain-security.

### Throttled

```python
Throttled(scope: str, rate: str, tiers: tuple[tuple[str, str], ...] = ())
```

Apply rate limiting via domain-api-limiter. Tiers are optional per-tier rate overrides, given as a tuple of `(tier, rate)` pairs.

### Monitored

```python
Monitored(event: str, sink=None, labels_from_result=None, labels_from_exc=None)
```

Emit metric events via domain-monitoring.

### WrapErrors

```python
WrapErrors(as_: type, catch: tuple[type[BaseException], ...] = (Exception,))
```

Translate exceptions to a target exception type via domain-errors.

### Retried

```python
Retried(policy=None, policy_from_request=None)
```

Retry with a static `RetryPolicy` (`policy=`) or a per-call selector (`policy_from_request=`). Exactly one of the two must be given. A selector that returns `None` for a call makes that call single-attempt.

### RequireMixins

```python
RequireMixins(bases: tuple[type, ...])
```

Class-only validation marker. Decoration fails with `ValueError` when the decorated class does not inherit every listed base. It adds no runtime wrapper.

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
)
def method(self) -> None:
    pass
```

## Error Handling

Declaration-time validation raises `AspectDeclarationError` when:

- Duplicate aspect kinds (e.g., two Logged entries).
- Unknown entry type (not one of the bundled entry types).
- Empty declaration (frozenset or argument list with no entries).

Entry objects reject invalid field values with `ValueError` when constructed. A missing optional dependency raises `ImportError` with a message naming the package or extra to install.

## Dependencies

Install every optional dependency with the `all` extra:

```bash
pip install domain-suite[all]
```

## Ordering

Aspects apply in this order, outermost first:

1. LOGGED (emits start, end and error events around everything else)
2. REQUIRES (permission check)
3. TENANT_SCOPED (tenant boundary enforcement)
4. THROTTLED (rate limiting)
5. MONITORED (metric emission)
6. WRAP_ERRORS (exception translation)
7. RETRIED (innermost: retries see the raw exceptions before WRAP_ERRORS converts them)

This order is enforced by the Aspects service during composition, regardless of the order you declare entries.
