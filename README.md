# monitoring-suite

Formerly domain-suite. Imports moved under the `monitoring_suite` root (see the 0.7.0 changelog entry for the map).

Consolidated domain packages for Python services: typed errors, security context, API rate limiting, event monitoring, and cross-cutting aspects.

[![PyPI](https://img.shields.io/pypi/v/monitoring-suite.svg)](https://pypi.org/project/monitoring-suite/)
[![CI](https://github.com/jekhator/monitoring-suite/workflows/CI/badge.svg)](https://github.com/jekhator/monitoring-suite/actions)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/monitoring-suite.svg)](https://pypi.org/project/monitoring-suite/)

## Overview

**monitoring-suite** brings together five complementary domain packages into a single distribution:

- **monitoring_suite.errors**: Typed domain error hierarchy with wrapping and chaining
- **monitoring_suite.security**: Security context management and authorization checks
- **monitoring_suite.api_limiter**: Request rate limiting and quota enforcement
- **monitoring_suite.monitoring**: Event monitoring and telemetry
- **monitoring_suite.aspects**: Composable decorators for logging, auth, throttling, monitoring, retries, and error wrapping

Each package keeps its API under the single `monitoring_suite` import root; the consolidation is organizational (single distribution, unified testing).

## Installation

```bash
# Base install (every package imports; no correlation labels on metrics)
uv add monitoring-suite

# With all optional extras (logging + sensitivity)
uv add "monitoring-suite[all]"

# Or select extras
uv add "monitoring-suite[logging]"    # for logging-suite support (Logged, Retried, correlation labels)
uv add "monitoring-suite[sensitivity]" # for logging-suite support
```

or with pip:

```bash
pip install monitoring-suite
pip install "monitoring-suite[all]"
```

Requires Python 3.12+.

## Packages

### monitoring_suite.errors

Typed domain error hierarchy with wrapping and chaining for Python services.

**Public API:**
`DomainError`, `ErrorChain`, `WrapErrorsClient`, `wrap_errors`, `ChainLink`, `ChainVia`, `DomainClassifier`, `DomainCrossing`.

**Example:**

```python
from monitoring_suite.errors import DomainError, wrap_errors

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

**Output (Python 3.11+, monitoring-suite==0.5.0):**
```
Error domain: database, code: db_connection_failed, http_status: 503, retryable: True
```

See `docs/monitoring_suite/errors/` for full documentation.

### monitoring_suite.security

Security context management and authorization checks.

**Public API:**
`SecurityContext`, `SecurityContextManager`, `Principal`, `requires`, `tenant_scoped`, `Authorizer`, `Permission`, `PolicyDecision`, `SecretRef`, `SecretValue`, security error classes.

**Example:**

```python
from monitoring_suite.security import Principal, SecurityContext, SecurityContextManager, requires

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

**Output (Python 3.11+, monitoring-suite==0.5.0):**
```
Admin access granted
```

See `docs/monitoring_suite/security/` for full documentation.

### monitoring_suite.api_limiter

Request rate limiting and quota enforcement.

**Public API:**
`throttled`, `PolicyRegistry`, `RateLimit`, `ThrottlePolicy`, `TierRate`, `Period`, `RateLimitExceeded`, throttle error classes.

**Example:**

```python
from monitoring_suite.api_limiter import throttled

@throttled(scope="api.documents", rate="100/hour")
def create_document(title: str):
    return {"id": "doc_123", "title": title}

result = create_document("My Document")
print(result)
```

**Output (Python 3.11+, monitoring-suite==0.5.0):**
```
{'id': 'doc_123', 'title': 'My Document'}
```

See `docs/monitoring_suite/api_limiter/` for full documentation.

### monitoring_suite.monitoring

Event monitoring and telemetry.

**Public API:**
`monitored`, `MonitorRegistry`, `MetricSink`, `MetricEvent`, `Outcome`, `CollectingSink`, `NullSink`, monitoring error classes.

**Example:**

```python
from monitoring_suite.monitoring import monitored

@monitored(event="document.processed")
def process_document(doc_id: str):
    return {"status": "success"}

result = process_document("doc_123")
print(result)
```

**Output (Python 3.11+, monitoring-suite==0.5.0):**
```
{'status': 'success'}
```

See `docs/monitoring_suite/monitoring/` for full documentation.

### monitoring_suite.aspects

Composable decorators for logging, auth, throttling, monitoring, retries, and error wrapping.

**Public API:**
`aspects`, `Logged`, `Monitored`, `Requires`, `Retried`, `RequireMixins`, `Throttled`, `TenantScoped`, `WrapErrors`, `AspectEntry`, `AspectKind`, aspect error classes.

**Example:**

```python
from monitoring_suite.aspects import aspects, Logged, Throttled
from monitoring_suite.security import Principal, SecurityContextManager
from logging_suite.logging import LoggingMixin

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

**Output (Python 3.11+, monitoring-suite==0.5.0):**
```
{'id': 'doc_123', 'title': 'My Doc'}
```

See `docs/monitoring_suite/aspects/` for full documentation.

## Consolidated From

This distribution consolidates five independent domain packages (`monitoring_suite.errors`, `monitoring_suite.security`, `monitoring_suite.api_limiter`, `monitoring_suite.monitoring`, and `monitoring_suite.aspects`) into a single unified distribution to simplify dependency management and testing.

Each package retains its original public API and namespace. Internal dependencies between packages within the suite are resolved locally (no external package re-imports required).

## Optional Extras

- **`[logging]`**: Integrates with `logging-suite>=0.7.0` for structured event logging adapters.
- **`[sensitivity]`**: Integrates with `logging-suite>=0.7.0` for automatic PII/PHI field masking.
- **`[all]`**: Includes logging-suite and boto3.

Future versions may introduce new extras or migrate integrations (e.g., if logging-suite consolidates further).

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
mypy
```

## License

Apache License 2.0. See LICENSE for details.

## Contributing

See CONTRIBUTING.md for guidelines.
