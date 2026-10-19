# Error Types and Semantics

## Purpose

The error hierarchy in domain-api-limiter provides typed, recoverable errors for rate-limit declaration and enforcement. All errors inherit from `domain-errors` DomainError, which integrates with structured logging, error tracking, and framework error-handling middleware. Errors are raised at different stages: `ThrottleDeclarationError` at import time when policies are malformed, and `RateLimitExceeded` at runtime when enforced by consuming frameworks.

## Behavior

### Error Hierarchy

```
DomainError
  `-- ThrottleError
        |-- RateLimitExceeded
        `-- ThrottleDeclarationError
```

All errors are instances of `DomainError` from domain-errors, which means:
- Errors carry a `domain` string ("api_limiter").
- Errors carry a `code` string identifying the specific error.
- Errors carry an HTTP status code for REST frameworks.
- Errors carry a `retryable` boolean indicating whether the client can safely retry.
- Errors preserve `__cause__` when wrapping exceptions, enabling root-cause analysis.
- Errors integrate with structured logging: logged errors expose domain, code, http_status, and retryable fields.

### ThrottleError

Base error for all rate-limit domain failures.

```python
from domain_api_limiter import ThrottleError

class ThrottleError(DomainError):
    domain = "api_limiter"
    code = "throttle_error"
    http_status = 429  # Too Many Requests
    retryable = True   # Transient failure; safe to retry
    default_message = "Rate limit constraint violated."
```

You rarely raise or catch ThrottleError directly; use the more specific subclasses.

### RateLimitExceeded

Raised by consuming frameworks when a rate limit is violated at runtime.

```python
from domain_api_limiter import RateLimitExceeded

class RateLimitExceeded(ThrottleError):
    code = "rate_limit_exceeded"
    http_status = 429  # Too Many Requests
    retryable = True   # Safe to retry
    default_message = "Rate limit exceeded."
```

HTTP status 429 signals to clients that they have exceeded a rate limit and should back off. The `retryable=True` flag indicates this is a transient failure: clients can retry the request after waiting (exponential backoff is recommended).

Example integration with Django REST Framework:

```python
from domain_api_limiter import RateLimitExceeded
from rest_framework.response import Response
from rest_framework.exceptions import Throttled

def check_rate_limit(policy, tier):
    # Pseudo-code: adapter checks if a rate limit is exceeded
    if exceeded:
        raise RateLimitExceeded(message="You have exceeded the rate limit for this operation.")
```

### ThrottleDeclarationError

Raised at decoration time when a policy declaration is invalid (wrong rate format, empty scope, etc.).

```python
from domain_api_limiter import ThrottleDeclarationError

class ThrottleDeclarationError(ThrottleError):
    code = "throttle_declaration_invalid"
    http_status = 500  # Internal Server Error
    retryable = False  # Configuration error; do not retry
    default_message = "Invalid throttle declaration."
```

HTTP status 500 signals a server-side configuration error: the service is misconfigured. The `retryable=False` flag tells clients and error-handling middleware not to retry; the error must be fixed in source code.

Example:

```python
from domain_api_limiter import throttled, ThrottleDeclarationError

try:
    @throttled("scope", "invalid_rate")  # Malformed rate
    def bad_method():
        pass
except ThrottleDeclarationError as e:
    print(f"Invalid policy: {e.message}")  # "rate must use the N/period form"
    print(f"HTTP status: {e.http_status}")  # 500
    print(f"Retryable: {e.retryable}")      # False
```

## Public Surface

### ThrottleError

```python
class ThrottleError(DomainError):
    domain: str = "api_limiter"
    code: str = "throttle_error"
    http_status: int = 429
    retryable: bool = True
    default_message: str = "Rate limit constraint violated."
```

### RateLimitExceeded

```python
class RateLimitExceeded(ThrottleError):
    code: str = "rate_limit_exceeded"
    http_status: int = 429
    retryable: bool = True
    default_message: str = "Rate limit exceeded."
```

### ThrottleDeclarationError

```python
class ThrottleDeclarationError(ThrottleError):
    code: str = "throttle_declaration_invalid"
    http_status: int = 500
    retryable: bool = False
    default_message: str = "Invalid throttle declaration."
```

All errors inherit from `DomainError` and support:
- `message` (str): Error message, often specific to the incident.
- `__cause__` (Exception | None): Root cause if the error wraps another exception.
- `context()` (dict): Additional metadata (e.g., rate, scope) attached via constructor kwargs.

## Error Messages and Constants

Errors raised during policy validation include specific messages via `domain_api_limiter.services.constants.policy`:

```python
ERR_POLICY_REQUESTS_NOT_POSITIVE = "rate requests must be positive"
ERR_POLICY_RATE_FORMAT = "rate must use the N/period form"
ERR_POLICY_UNKNOWN_PERIOD = "unknown rate period"
ERR_POLICY_EMPTY_TIER = "tier label must be non-empty"
ERR_POLICY_EMPTY_SCOPE = "scope must be non-empty"
ERR_POLICY_DUPLICATE_TIERS = "tier labels must be unique"
```

These messages are used in `ThrottleDeclarationError` exceptions raised during policy construction.

## Error Semantics

### Declaration Errors (at import time)

When the `@throttled` decorator or policy value objects detect invalid input, they raise `ThrottleDeclarationError` immediately. This ensures that invalid configurations fail at startup, never silently at runtime.

| Condition | Error Message | HTTP Status | Retryable |
|-----------|---------------|-------------|-----------|
| Negative or zero request count | rate requests must be positive | 500 | False |
| Malformed rate string (e.g., "invalid") | rate must use the N/period form | 500 | False |
| Unknown period (e.g., "century") | unknown rate period | 500 | False |
| Empty scope | scope must be non-empty | 500 | False |
| Empty tier label | tier label must be non-empty | 500 | False |
| Duplicate tier labels | tier labels must be unique | 500 | False |

### Enforcement Errors (at runtime)

When a consuming framework detects that a rate limit has been exceeded, it raises `RateLimitExceeded` to signal the client to back off.

| Condition | Error Type | HTTP Status | Retryable |
|-----------|------------|-------------|-----------|
| Rate limit exceeded | RateLimitExceeded | 429 | True |

## Example Usage

### Catching Declaration Errors

```python
from domain_api_limiter import ThrottleDeclarationError, throttled

# Malformed rate string
try:
    @throttled("scope", "not_a_rate")
    def bad_method():
        pass
except ThrottleDeclarationError as e:
    print(f"Error: {e.message}")  # "rate must use the N/period form"
    print(f"Code: {e.code}")       # "throttle_declaration_invalid"
    print(f"Status: {e.http_status}")  # 500

# Empty scope
try:
    @throttled("", "100/hour")
    def another_bad_method():
        pass
except ThrottleDeclarationError as e:
    print(f"Error: {e.message}")  # "scope must be non-empty"

# Duplicate tier labels
try:
    @throttled(
        "scope",
        "100/hour",
        tiers={"free": "10/day", "free": "5/day"}  # Duplicate "free"
    )
    def yet_another_bad():
        pass
except ThrottleDeclarationError as e:
    print(f"Error: {e.message}")  # "tier labels must be unique"
```

### Handling Enforcement Errors

```python
from domain_api_limiter import RateLimitExceeded

# In a Django REST Framework throttle or middleware
try:
    # Check rate limit (pseudo-code)
    if rate_limit_exceeded:
        raise RateLimitExceeded(
            message="You have exceeded 100 requests per hour.",
            scope="docs:list",
            tier="free"
        )
except RateLimitExceeded as e:
    # Client sees HTTP 429
    print(f"Error: {e.message}")      # "You have exceeded 100 requests per hour."
    print(f"Code: {e.code}")          # "rate_limit_exceeded"
    print(f"Status: {e.http_status}") # 429
    print(f"Retryable: {e.retryable}") # True
    
    # Middleware or framework returns:
    # HTTP 429 Too Many Requests
    # Retry-After: 3600 (1 hour)
```

### Structured Logging Integration

All domain-api-limiter errors integrate with structured logging via domain-errors:

```python
from domain_api_limiter import ThrottleDeclarationError
import structlog

logger = structlog.get_logger()

try:
    @throttled("scope", "-5/hour")
    def bad():
        pass
except ThrottleDeclarationError as e:
    # Logged with domain, code, http_status, retryable
    logger.exception(
        "policy_declaration_failed",
        error=e,
        scope=e.context().get("scope"),
        rate=e.context().get("rate"),
    )
    # Structured log includes:
    # {
    #   "message": "policy_declaration_failed",
    #   "error.domain": "api_limiter",
    #   "error.code": "throttle_declaration_invalid",
    #   "error.http_status": 500,
    #   "error.retryable": false,
    #   "scope": "scope",
    #   "rate": "-5/hour"
    # }
```

## See Also

- [Throttle Policy Objects](policy.md) for validation details and what errors are raised during policy creation.
- [@throttled Decorator](throttled.md) for examples of decoration-time error handling.
- [domain-errors](https://github.com/jekhator/domain-errors) for details on DomainError structure and integration.
