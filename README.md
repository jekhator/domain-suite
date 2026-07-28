# domain-suite

Consolidated domain packages for Python services: typed errors, security context, API rate limiting, event monitoring, and cross-cutting aspects.

[![PyPI](https://img.shields.io/pypi/v/domain-suite.svg)](https://pypi.org/project/domain-suite/)
[![CI](https://github.com/jekhator/domain-suite/workflows/CI/badge.svg)](https://github.com/jekhator/domain-suite/actions)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/domain-suite.svg)](https://pypi.org/project/domain-suite/)

## Overview

**domain-suite** brings together five complementary domain packages into a single distribution:

- **domain-errors**: Typed domain error hierarchy with wrapping and chaining
- **domain-security**: Security context management and authorization checks
- **domain-api-limiter**: Request rate limiting and quota enforcement
- **domain-monitoring**: Event monitoring and telemetry
- **domain-aspects**: Composable decorators for logging, auth, throttling, error wrapping, and sensitivity masking

Each package maintains its namespace and API; the consolidation is organizational (single distribution, unified testing).

## Installation

```bash
# Base install
uv add domain-suite

# With all optional extras (logging + sensitivity)
uv add "domain-suite[all]"

# Or select extras
uv add "domain-suite[logging]"    # for mixin-logging support
uv add "domain-suite[sensitivity]" # for mixin-sensitivity support
```

or with pip:

```bash
pip install domain-suite
pip install "domain-suite[all]"
```

Requires Python 3.11+.

## Packages

### domain-errors

Typed domain error hierarchy with wrapping and chaining for Python services.

**Public API:**
`DomainError`, `ErrorChain`, `WrapErrorsClient`, `wrap_errors`, `ChainLink`, `ChainVia`, `DomainClassifier`, `DomainCrossing`.

**Example:**

```python
from domain_errors import DomainError, wrap_errors

class DatabaseError(DomainError):
    domain = "database"
    code = "db_connection_failed"
    http_status = 503
    retryable = True

@wrap_errors(as_=DatabaseError)
def fetch_user(user_id: str):
    raise RuntimeError(f"Database connection failed for {user_id}")

try:
    fetch_user("usr_123")
except DatabaseError as e:
    print(f"Error domain: {e.domain}, code: {e.code}, http_status: {e.http_status}, retryable: {e.retryable}")
```

**Output (Python 3.11+, domain-suite==0.5.0):**
```
Error domain: database, code: db_connection_failed, http_status: 503, retryable: True
```

See `docs/domain_errors/` for full documentation.

### domain-security

Security context management and authorization checks.

**Public API:**
`SecurityContext`, `SecurityContextManager`, `Principal`, `requires`, `tenant_scoped`, `Authorizer`, `Permission`, `PolicyDecision`, `SecretRef`, `SecretValue`, security error classes.

**Example:**

```python
from domain_security import Principal, SecurityContext, SecurityContextManager, requires

# Create principal with required scope
principal = Principal(id="usr_123", scopes=frozenset(["admin.read"]))
ctx = SecurityContext(principal=principal, tenant_id="org_abc")

# Bind context for a request scope
manager = SecurityContextManager()
with manager.bind(principal=principal, tenant_id="org_abc"):
    # Enforce authorization via decorator
    @requires(permission="admin.read")
    def admin_only_function():
        return "Admin access granted"
    
    result = admin_only_function()
    print(result)
```

**Output (Python 3.11+, domain-suite==0.5.0):**
```
Admin access granted
```

See `docs/domain_security/` for full documentation.

### domain-api-limiter

Request rate limiting and quota enforcement.

**Public API:**
`throttled`, `PolicyRegistry`, `RateLimit`, `ThrottlePolicy`, `TierRate`, `Period`, `RateLimitExceeded`, throttle error classes.

**Example:**

```python
from domain_api_limiter import throttled

@throttled(scope="api.documents", rate="100/hour")
def create_document(title: str):
    return {"id": "doc_123", "title": title}

result = create_document("My Document")
print(result)
```

**Output (Python 3.11+, domain-suite==0.5.0):**
```
{'id': 'doc_123', 'title': 'My Document'}
```

See `docs/domain_api_limiter/` for full documentation.

### domain-monitoring

Event monitoring and telemetry.

**Public API:**
`monitored`, `MonitorRegistry`, `MetricSink`, `MetricEvent`, `Outcome`, `CollectingSink`, `NullSink`, monitoring error classes.

**Example:**

```python
from domain_monitoring import monitored

@monitored(event="document.processed")
def process_document(doc_id: str):
    return {"status": "success"}

result = process_document("doc_123")
print(result)
```

**Output (Python 3.11+, domain-suite==0.5.0):**
```
{'status': 'success'}
```

See `docs/domain_monitoring/` for full documentation.

### domain-aspects

Composable decorators for logging, auth, throttling, error wrapping, and sensitivity masking.

**Public API:**
`aspects`, `Logged`, `Requires`, `Throttled`, `TenantScoped`, `WrapErrors`, `Sensitive`, `AspectEntry`, `AspectKind`, aspect error classes.

**Example:**

```python
from domain_aspects import aspects, Logged, Throttled
from domain_security import Principal, SecurityContextManager
from mixin_logging import LoggingMixin

class DocumentService(LoggingMixin):
    @aspects(
        Logged(event="document.create"),
        Throttled(scope="api.documents", rate="100/hour"),
    )
    def create_document(self, title: str, content: str) -> dict:
        return {"id": "doc_123", "title": title}

principal = Principal(id="usr_123")
manager = SecurityContextManager()
with manager.bind(principal=principal, tenant_id="org_abc"):
    service = DocumentService()
    result = service.create_document("My Doc", "Content here")
    print(result)
```

**Output (Python 3.11+, domain-suite==0.5.0):**
```
{'id': 'doc_123', 'title': 'My Doc'}
```

See `docs/domain_aspects/` for full documentation.

## Consolidated From

This distribution consolidates five independent domain packages (originally `domain-errors`, `domain-security`, `domain-api-limiter`, `domain-monitoring`, and `domain-aspects`) into a single unified distribution to simplify dependency management and testing.

Each package retains its original public API and namespace. Internal dependencies between packages within the suite are resolved locally (no external package re-imports required).

## Optional Extras

- **`[logging]`**: Integrates with `mixin-suite>=0.5.0` for structured event logging adapters.
- **`[sensitivity]`**: Integrates with `mixin-suite>=0.5.0` for automatic PII/PHI field masking.
- **`[all]`**: Includes both mixin-suite packages.

Future versions may introduce new extras or migrate integrations (e.g., `mixin-suite` packages if they consolidate similarly).

## Development

Install development dependencies:

```bash
uv sync --all-extras
```

Run tests:

```bash
uv run pytest
```

Run linting and type checking:

```bash
ruff check .
ruff format --check .
mypy
```

## License

Apache License 2.0. See LICENSE for details.

## Contributing

See CONTRIBUTING.md for guidelines.
