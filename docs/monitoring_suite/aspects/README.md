# monitoring_suite.aspects

Composable decorators for logging, auth, throttling, error wrapping, and sensitivity masking.

## Overview

`monitoring_suite.aspects` provides:

- **Aspect composition**: Stack multiple cross-cutting concerns on a function
- **Declarative syntax**: Use `@aspects(...)` to apply multiple decorators atomically
- **Pre-built aspects**: Logged, Requires, Throttled, TenantScoped, WrapErrors, Sensitive
- **Extensible design**: Create custom aspects by implementing the AspectEntry interface

## Quick Start

```python
from monitoring_suite.aspects import aspects, Logged, Requires, Throttled

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
- **`Logged`**: Event logging aspect (from monitoring_suite.monitoring)
- **`Requires`**: Authorization aspect (from monitoring_suite.security)
- **`Throttled`**: Rate limiting aspect (from monitoring_suite.api_limiter)
- **`TenantScoped`**: Tenant isolation aspect (from monitoring_suite.security)
- **`WrapErrors`**: Error wrapping aspect (from monitoring_suite.errors)
- **`Sensitive`**: Sensitivity masking aspect (from mixin-sensitivity)
- **`AspectEntry`**: Base interface for custom aspects
- **`AspectKind`**: Enum of aspect types
- Aspect error classes: `AspectsError`, `AspectDeclarationError`

## Features

### Per-Feature Documentation

Detailed documentation for aspect composition:

- **[aspects/aspects.md](apps/aspects/aspects.md)**: Aspect decorator details and composition rules

### Architecture & Design

- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before monitoring-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Logging + Authorization + Throttling

```python
from monitoring_suite.aspects import aspects, Logged, Requires, Throttled

@aspects(
    Logged(event="api.documents.create"),
    Requires(permission="documents.write"),
    Throttled(scope="api.documents", rate="100/hour"),
)
def create_document(title: str, content: str) -> dict:
    # The decorator(s) automatically:
    # - Log start/success/error events
    # - Enforce permission checks before execution
    # - Track rate-limit quota
    # - Handle exceptions and re-raise
    return {"id": "doc_123", "title": title, "content": content}
```

### Tenant-Scoped Operations with Error Wrapping

```python
from monitoring_suite.aspects import aspects, TenantScoped, WrapErrors
from monitoring_suite.errors import DomainError

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
    return {"tenant": tenant_id, "data": {...}}
```

### Sensitivity Masking on Sensitive Data

```python
from monitoring_suite.aspects import aspects, Sensitive

@aspects(
    Sensitive(),
)
def get_user_with_ssn(user_id: str) -> dict:
    # The decorator automatically masks sensitive fields in repr()
    return {"user_id": user_id, "ssn": "123-45-6789"}  # ssn field marked @sensitive
```

## Aspect Order Matters

Aspects are applied in order. Common patterns:

1. **Error wrapping first**: Catch exceptions from downstream aspects
2. **Authorization second**: Fail fast before expensive operations
3. **Throttling third**: Track quota after auth passes
4. **Logging outermost**: Capture all events and times

```python
@aspects(
    WrapErrors(as_=APIError),      # Outermost: catch all exceptions
    Requires(permission="read"),   # Fail fast on auth
    Throttled(scope="api", rate="100/hour"),  # Track quota
    Logged(event="api.read"),      # Innermost: log the core operation
)
def read_data(resource_id: str):
    pass
```

## Custom Aspects

Extend `AspectEntry` to create custom cross-cutting concerns:

```python
from monitoring_suite.aspects import AspectEntry, AspectKind
from typing import Callable, Any

class CustomAspect(AspectEntry):
    kind = AspectKind.CUSTOM
    
    def __init__(self, name: str):
        self.name = name
    
    def apply(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            print(f"Before {self.name}")
            result = func(*args, **kwargs)
            print(f"After {self.name}")
            return result
        return wrapper
```

## Next Steps

- Read the [main monitoring-suite README](../../README.md) for installation and examples
- Explore feature documentation in [apps/aspects/](apps/aspects/)
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
- Review integration examples with individual domain packages above
