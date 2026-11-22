# monitoring_suite.errors. DomainError Base

> **Location:** `monitoring_suite/errors/docs/apps/domain_error.md`
> **Status:** Living reference. Core base class fully implemented in v0.1.0+.
> **Code location:** `monitoring_suite/errors/domains/domain_error/domain_error.py`
> **Constants:** `monitoring_suite/errors/domains/constants/domain_error.py`
> **Sibling docs:** `docs/apps/chain.md`, `docs/apps/diagrams.md`

## Purpose

`DomainError` is the base class for per-project typed exception hierarchies. It provides a lightweight contract for domain-specific errors: each error declares its code, domain, HTTP status, and retryability, enabling structured error handling, logging, and cross-domain tracing.

## The Class Variable Contract

Every `DomainError` subclass declares five class variables that define the error's contract:

### `code: str`

A short, unique identifier for the error. Used in logs, metrics, and API responses.

**Default:** `"domain_error"`
**Example:** `"auth_token_expired"`, `"validation_failed"`, `"resource_not_found"`

### `domain: str`

A namespace identifying which system/service owns the error. Enables cross-domain tracing and error classification.

**Default:** `"application"`
**Example:** `"auth"`, `"database"`, `"payment"`, `"document_processor"`

### `http_status: int`

The HTTP status code that represents this error when converted to an API response. Useful for automatic REST mapping.

**Default:** `500` (Internal Server Error)
**Example:** `400` (Bad Request), `401` (Unauthorized), `404` (Not Found), `503` (Service Unavailable)

### `retryable: bool`

Whether this error indicates a transient failure that may succeed on retry. Guides automatic retry logic in task queues and circuit breakers.

**Default:** `False`
**Example:** `True` for network timeouts; `False` for validation failures

### `default_message: str`

A human-readable fallback message shown when the error is raised without an explicit message.

**Default:** `"An unspecified domain error occurred."`
**Example:** `"The authentication token has expired. Please log in again."`, `"Database connection timed out. Retrying..."`

## Instance State

When instantiated, a `DomainError` stores two pieces of instance state:

### `message: str`

The specific error message for this occurrence. Either passed to `__init__` or defaults to the class `default_message`.

```python
raise DatabaseError(message="Connection to PostgreSQL timed out after 30s")
```

### `context: dict[str, object]`

A dictionary of structured context data (keyword arguments) that describe the error. Useful for logging, metrics, and debugging.

```python
raise PaymentError(
    message="Payment declined",
    transaction_id="txn_xyz789",
    amount_cents=5000,
    currency="USD",
    reason_code="insufficient_funds"
)
```

## Subclassing: Building a Taxonomy

To build a domain-specific error hierarchy, subclass `DomainError` and set the class variables:

```python
from monitoring_suite.errors import DomainError

class AuthError(DomainError):
    """Base for authentication errors."""
    domain = "auth"

class TokenExpiredError(AuthError):
    """Raised when a bearer token has expired."""
    code = "token_expired"
    http_status = 401
    retryable = False
    default_message = "Authentication token has expired."

class TokenValidationError(AuthError):
    """Raised when a token fails signature validation."""
    code = "token_validation_failed"
    http_status = 401
    retryable = False
    default_message = "Token signature is invalid."
```

Then raise with specific context:

```python
try:
    token = verify_jwt(auth_header)
except InvalidSignatureError as e:
    raise TokenValidationError(
        message=f"JWT validation failed: {e}",
        token_kid=token.kid,
        algorithm=token.header.alg
    ) from e
```

## Message and Context

### Message Semantics

- If `message=None` is passed to `__init__`, the instance message defaults to `default_message`.
- If `message=""` (empty string) is passed, the instance message is the empty string (not the default).
- If `message="custom"` is passed, the instance message is `"custom"`.

```python
# Uses default_message
error1 = DatabaseError()
assert error1.message == "An unspecified domain error occurred."

# Custom message
error2 = DatabaseError(message="PostgreSQL is down")
assert error2.message == "PostgreSQL is down"
```

### Context as Keyword Arguments

All keyword arguments passed to `__init__` (after `message`) are collected into `context`:

```python
error = PaymentError(
    message="Payment declined",
    transaction_id="txn_xyz789",
    amount_cents=5000
)

assert error.context == {
    "transaction_id": "txn_xyz789",
    "amount_cents": 5000
}
```

Context is **not** included in the exception's string representation; it is intended for structured logging only.

## Usage Example

Here's a minimal service with typed errors:

```python
from monitoring_suite.errors import DomainError

class DatabaseError(DomainError):
    domain = "database"
    http_status = 503
    retryable = True
    default_message = "Database operation failed."

class ValidationError(DomainError):
    domain = "validation"
    http_status = 400
    retryable = False
    default_message = "Input validation failed."

def fetch_user(user_id: str) -> dict:
    """Fetch a user by ID, raising domain errors on failure."""
    if not user_id:
        raise ValidationError(
            message="user_id cannot be empty",
            field="user_id"
        )
    
    try:
        # ... database query
        pass
    except Exception as e:
        raise DatabaseError(
            message=f"Failed to fetch user {user_id}: {e}",
            user_id=user_id
        ) from e

def handle_request(request):
    """HTTP handler that catches domain errors."""
    try:
        user = fetch_user(request.query_params.get("user_id"))
        return {"status": 200, "user": user}
    except DomainError as err:
        # Use the contract to map to HTTP response
        return {
            "status": err.http_status,
            "code": err.code,
            "message": err.message,
        }
```

## Integration with ErrorChain

`DomainError` integrates with `ErrorChain` for exception tracing and cross-domain causation tracking. See `docs/apps/chain.md` for chaining patterns and structured logging.

## Design Notes

- **No inheritance on data classes:** `DomainError` is a pure contract carrier, not a mixin. No other inheritance required.
- **Immutable contract:** Class variables are declarations, not instance-specific configuration. All configuration happens at subclass definition time.
- **Structured context, not message embedding:** Use `context` dict for metrics-ready data; avoid concatenating values into `message`.
- **Exceptions are not control flow:** Use domain errors for exceptional conditions only, not for normal branching.

## See Also

- **Error Chaining Reference:** `docs/apps/chain.md`
- **Architecture:** `docs/apps/diagrams.md`
