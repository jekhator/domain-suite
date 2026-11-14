# domain-aspects

Composable decorators for logging, authorization, tenancy, throttling, metric emission, error wrapping, retries, and mixin validation.

## Overview

`domain-aspects` provides:

- **Aspect composition**: Stack multiple cross-cutting concerns on a function or class
- **Declarative syntax**: Use `@aspects(...)` to apply multiple decorators in one declaration
- **Fixed ordering**: Concerns apply in a documented order regardless of declaration order
- **Validation at decoration time**: Duplicate kinds and unknown entries fail before anything runs

## Quick Start

```python
from domain_aspects import aspects, Logged, Requires, Throttled

# Compose multiple concerns on a single function
@aspects(
    Logged(event="document.create"),
    Requires(permission="documents.write"),
    Throttled(scope="api.documents", rate="100/hour"),
)
def create_document(title: str, content: str) -> dict:
    return {"id": "doc_123", "title": title}
```

## Public API

- **`aspects`**: Decorator to compose multiple aspect concerns
- **`Logged`**: Event logging aspect (mixin-logging)
- **`Requires`**: Authorization aspect (domain-security)
- **`TenantScoped`**: Tenant isolation aspect (domain-security)
- **`Throttled`**: Rate limiting aspect (domain-api-limiter)
- **`Monitored`**: Metric emission aspect (domain-monitoring)
- **`WrapErrors`**: Error wrapping aspect (domain-errors)
- **`Retried`**: Retry aspect with a static or per-call policy (mixin-retry)
- **`RequireMixins`**: Class-only validation that a class inherits required bases
- **`AspectEntry`**: Union type of all entry types
- **`AspectKind`**: Enum of aspect kinds
- **`ASPECT_ORDER`**: The fixed application order
- Aspect error classes: `AspectsError`, `AspectDeclarationError`

## Features

### Per-Feature Documentation

Detailed documentation for aspect composition:

- **[aspects/aspects.md](apps/aspects/aspects.md)**: Aspect decorator details and composition rules

### Architecture & Design

- **[flow-trace.md](architecture/flow-trace.md)**: Composition and call flow
- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before domain-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Logging + Authorization + Throttling

```python
from domain_aspects import aspects, Logged, Requires, Throttled

@aspects(
    Logged(event="api.documents.create"),
    Requires(permission="documents.write"),
    Throttled(scope="api.documents", rate="100/hour"),
)
def create_document(title: str, content: str) -> dict:
    # The decorator(s) automatically:
    # - Log start/end/error events
    # - Enforce permission checks before execution
    # - Track rate-limit quota
    # - Re-raise exceptions unchanged
    return {"id": "doc_123", "title": title, "content": content}
```

### Tenant-Scoped Operations with Error Wrapping

```python
from domain_aspects import aspects, TenantScoped, WrapErrors
from domain_errors import DomainError

class DatabaseError(DomainError):
    domain = "database"
    code = "connection_failed"
    http_status = 503
    retryable = True

@aspects(
    TenantScoped(param_name="tenant_id"),
    WrapErrors(as_=DatabaseError),
)
def fetch_tenant_data(tenant_id: str):
    # The decorator(s) automatically:
    # - Verify tenant_id matches security context
    # - Wrap exceptions as DatabaseError
    return {"tenant": tenant_id, "data": {}}
```

### Retries with Error Wrapping

```python
from mixin_retry import RetryPolicy

from domain_aspects import aspects, Retried, WrapErrors

policy = RetryPolicy(
    max_attempts=3,
    backoff_base_seconds=0.1,
    backoff_multiplier=2.0,
    backoff_max_seconds=2.0,
    jitter=False,
    should_retry=lambda error: isinstance(error, TimeoutError),
)

@aspects(
    Retried(policy=policy),
    WrapErrors(as_=DatabaseError, catch=(TimeoutError,)),
)
def fetch_rows() -> list[str]:
    return []
```

Retries run inside WRAP_ERRORS, so a predicate sees the raw `TimeoutError`. Only the final failure is wrapped.

## Aspect Order

The application order is fixed by `ASPECT_ORDER`, outermost first:

1. LOGGED
2. REQUIRES
3. TENANT_SCOPED
4. THROTTLED
5. MONITORED
6. WRAP_ERRORS
7. RETRIED (innermost)

Declaration order does not matter. Reorder the list in the source and the composed behaviour stays the same.

## Writing Your Own Entries

`AspectEntry` is a closed union of the bundled entry types. Custom entry types are not supported by `aspects(...)`; use a plain decorator for a concern the suite does not cover.

## Next Steps

- Read the [main domain-suite README](../../README.md) for installation and examples
- Explore feature documentation in [apps/aspects/](apps/aspects/)
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
- Review integration examples with individual domain packages above
