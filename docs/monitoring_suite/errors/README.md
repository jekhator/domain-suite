# monitoring_suite.errors

Typed domain error hierarchy with wrapping and chaining for Python services.

## Overview

`monitoring_suite.errors` provides:

- **DomainError base class**: Structured exception hierarchy with domain, code, HTTP status, and retryable flag
- **Error wrapping**: Convert third-party library exceptions to typed domain errors
- **Error chaining**: Preserve exception causality while translating between layers
- **Classification**: Categorize exceptions by origin (Python stdlib, HTTP client, AWS SDK, etc.)

## Quick Start

```python
from monitoring_suite.errors import DomainError, wrap_errors

# Define a domain error
class DatabaseError(DomainError):
    domain = "database"
    code = "connection_failed"
    http_status = 503
    retryable = True

# Wrap exceptions with @wrap_errors decorator
@wrap_errors(as_=DatabaseError)
def fetch_user(user_id: str):
    # ... implementation that may raise psycopg2.OperationalError
    pass
```

## Public API

- **`DomainError`**: Base exception class for all domain errors
- **`ErrorChain`**: Chain multiple errors with causality tracking
- **`wrap_errors`**: Decorator to catch and wrap exceptions
- **`WrapErrorsClient`**: Low-level error wrapping client
- **`ChainLink`, `ChainVia`, `DomainClassifier`, `DomainCrossing`**: DTO classes for error chain serialization

## Features

### Per-Feature Documentation

Detailed documentation for each feature:

- **[chain.md](apps/chain.md)**: Error chaining and causality preservation
- **[domain_error.md](apps/domain_error.md)**: DomainError base class and subclass patterns
- **[python.md](apps/python.md)**: Stdlib exception classification
- **[http.md](apps/http.md)**: HTTP client exception classification
- **[cloud.md](apps/cloud.md)**: AWS SDK exception classification
- **[wrap_errors.md](apps/wrap_errors.md)**: Exception wrapping decorator

### Architecture & Design

- **[diagrams.md](apps/diagrams.md)**: Visual guides to error hierarchy and chaining
- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before monitoring-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Error Classification

monitoring_suite.errors includes pre-built classifiers for common exception sources:

- **Python stdlib**: `ValueError`, `TypeError`, `KeyError`, etc.
- **HTTP clients**: `httpx.HTTPError`, `requests.RequestException`, etc.
- **AWS SDK**: `botocore.ClientError`, `boto3` exceptions, etc.

## Integration with monitoring_suite.aspects

Use the `@WrapErrors` aspect in monitoring_suite.aspects for declarative error wrapping:

```python
from monitoring_suite.aspects import aspects, WrapErrors

@aspects(
    WrapErrors(as_=DatabaseError),
)
def fetch_user(user_id: str):
    pass
```

## Next Steps

- Read the [main monitoring-suite README](../../README.md) for installation and examples
- Choose a feature from the list above and read its detailed documentation
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
