# domain-errors. ErrorChain

> **Location:** `domain_errors/docs/apps/chain.md`
> **Status:** Living reference. Core chaining fully implemented in v0.1.0+.
> **Code location:** `domain_errors/services/chain/` (`chain_client.py`, `chain_objects.py`)
> **Constants:** `domain_errors/services/constants/chain.py`
> **Sibling docs:** `docs/apps/domain_error.md`, `docs/apps/diagrams.md`

## Purpose

`ErrorChain` walks exception causation chains (via `__cause__` and `__context__`) to build structured traces of errors across domain boundaries. It detects when errors cross from one domain to another, resolves domains for foreign (non-DomainError) exceptions, and produces logging-ready DTOs for audit trails.

## Core Operations

`ErrorChain` provides three static methods:

### `wrap(err, as_=SomeError, message=None, **context) -> SomeError`

Construct a typed domain error for the caller to raise with `from err`.

**Purpose:** Convert a foreign exception into a typed domain error, preserving the exception chain.

**Signature:**
```python
@staticmethod
def wrap(
    err: Exception,
    *,
    as_: type[TypeDomainError],
    message: str | None = None,
    **context: object,
) -> TypeDomainError
```

**Parameters:**
- `err`: the caught exception to wrap
- `as_`: the target DomainError subclass
- `message`: optional custom message (defaults to the class `default_message`)
- `**context`: structured context data (e.g., `user_id=123, attempt=2`)

**Example:**
```python
from domain_errors import DomainError, ErrorChain

class DatabaseError(DomainError):
    code = "db_query_failed"
    domain = "database"
    http_status = 503
    retryable = True
    default_message = "Database query failed."

try:
    result = db.query("SELECT * FROM users WHERE id = $1", user_id)
except psycopg2.OperationalError as e:
    raise ErrorChain.wrap(
        e,
        as_=DatabaseError,
        message=f"Query timed out after 30s",
        query="SELECT * FROM users WHERE id = $1",
        user_id=user_id
    ) from e
```

**Behavior:** Returns an instance of `as_` initialized with the provided `message` and `context`. Does not modify the exception chain; the caller must use `raise ... from e` to link it.

### `history(err, classifiers=()) -> tuple[ChainLink, ...]`

Walk the full exception cascade into a sequence of links.

**Purpose:** Extract and structure the entire exception chain for logging or debugging.

**Signature:**
```python
@staticmethod
def history(
    err: BaseException,
    classifiers: tuple[DomainClassifier, ...] = (),
) -> tuple[ChainLink, ...]
```

**Parameters:**
- `err`: the root exception (typically the caught exception in an except block)
- `classifiers`: optional domain classifiers to resolve domains for foreign exceptions

**Returns:** A tuple of `ChainLink` objects, root exception first, following `__cause__` (CAUSE via) then `__context__` (CONTEXT via) unless suppressed.

**Example:**
```python
try:
    result = await fetch_from_api(user_id)
except Exception as e:
    links = ErrorChain.history(e)
    for link in links:
        print(f"{link.type_name}: {link.message} (domain={link.domain})")
        # Output:
        # APITimeoutError: Connection timed out (domain=api)
        # TimeoutError: [Errno 110] Connection timed out (domain=python)
```

**Behavior:**
- Walks the exception chain via `__cause__` first, then `__context__` (unless `__suppress_context__` is set).
- Detects cycles (if the same exception object appears twice) and stops.
- For each link, resolves the domain from the exception's `domain` attribute (if a DomainError), or the first matching classifier, or falls back to `"python"`.
- Records the `via` tag (ROOT, CAUSE, or CONTEXT) for each link.

### `crossings(err, classifiers=()) -> tuple[DomainCrossing, ...]`

Identify causation hops where the cascade crossed domains.

**Purpose:** Find where errors changed domain (e.g., a database error caused an API error), useful for audit trails and dependency mapping.

**Signature:**
```python
@staticmethod
def crossings(
    err: BaseException,
    classifiers: tuple[DomainClassifier, ...] = (),
) -> tuple[DomainCrossing, ...]
```

**Parameters:**
- `err`: the root exception
- `classifiers`: optional domain classifiers

**Returns:** A tuple of `DomainCrossing` objects, one for each link-to-link transition where domains differ.

**Example:**
```python
try:
    result = await fetch_from_api(user_id)
except Exception as e:
    crossings = ErrorChain.crossings(e)
    for crossing in crossings:
        print(
            f"{crossing.cause.type_name} ({crossing.cause.domain}) "
            f"-> {crossing.effect.type_name} ({crossing.effect.domain})"
        )
        # Output:
        # TimeoutError (python) -> APITimeoutError (api)
```

**Behavior:**
- Compares adjacent links in the history; if domains differ, records the crossing.
- Crossings capture the cause and effect links, ready for structured logging.

## Value Objects

### `ChainVia` (StrEnum)

How a link entered the chain.

```python
class ChainVia(StrEnum):
    ROOT = "root"      # The initial exception
    CAUSE = "cause"    # Linked via __cause__ (explicit raise ... from)
    CONTEXT = "context"  # Linked via __context__ (implicit exception context)
```

### `ChainLink`

One hop of an exception chain, ready for structured logging.

```python
@dataclass(frozen=True, slots=True)
class ChainLink:
    type_name: str                    # Exception class name
    message: str                      # str(exception)
    code: str | None                  # DomainError.code if applicable
    domain: str                       # DomainError.domain or classifier verdict
    via: ChainVia                     # ROOT, CAUSE, or CONTEXT
    context: dict[str, object] = {}   # DomainError.context if applicable
```

**Methods:**
- `to_log_extra() -> dict[str, object]`: Convert to a JSON-ready dict for logger `extra` parameter.

### `DomainCrossing`

One causation hop where the error crossed from one domain to another.

```python
@dataclass(frozen=True, slots=True)
class DomainCrossing:
    cause: ChainLink      # The lower exception
    effect: ChainLink     # The higher exception
```

**Methods:**
- `to_log_extra() -> dict[str, object]`: Convert to a JSON-ready dict for logger `extra` parameter.

### `DomainClassifier` (Protocol)

A contract for classifying foreign exceptions (non-DomainError).

```python
class DomainClassifier(Protocol):
    def classify(self, err: BaseException) -> str | None:
        """Return the error's domain, or None when it is not this family."""
        ...
```

**Example implementation:**
```python
class PythonStdlibClassifier:
    def classify(self, err: BaseException) -> str | None:
        if isinstance(err, (TimeoutError, ConnectionError, IOError)):
            return "python"
        return None

class BotocoreClassifier:
    def classify(self, err: BaseException) -> str | None:
        if "botocore" in err.__class__.__module__:
            return "aws"
        return None
```

### Logging Payload DTOs

#### `LinkLogExtra`

Structured-logging payload for one chain link. Produced by `ChainLink.to_log_extra()`.

```python
@dataclass(frozen=True, slots=True)
class LinkLogExtra:
    type: str                       # Exception class name
    message: str                    # str(exception)
    code: str | None                # DomainError.code
    domain: str                     # Domain identifier
    via: str                        # "root", "cause", or "context"
    context: dict[str, object]      # Structured context
```

#### `CrossingLogExtra`

Structured-logging payload for one cross-domain crossing. Produced by `DomainCrossing.to_log_extra()`.

```python
@dataclass(frozen=True, slots=True)
class CrossingLogExtra:
    cause_type: str        # Cause exception class name
    cause_domain: str      # Cause domain
    effect_type: str       # Effect exception class name
    effect_domain: str     # Effect domain
```

## Plugging a Domain Classifier

To resolve domains for foreign exceptions, pass classifiers to `history()` or `crossings()`:

```python
class PythonStdlibClassifier:
    def classify(self, err: BaseException) -> str | None:
        if isinstance(err, (TimeoutError, ConnectionError)):
            return "stdlib"
        return None

class BotocoreClassifier:
    def classify(self, err: BaseException) -> str | None:
        if "botocore" in err.__class__.__module__:
            return "aws"
        return None

try:
    result = await fetch_from_api()
except Exception as e:
    classifiers = (PythonStdlibClassifier(), BotocoreClassifier())
    
    links = ErrorChain.history(e, classifiers=classifiers)
    for link in links:
        logger.error(
            "Exception in chain",
            extra=link.to_log_extra()
        )
    
    crossings = ErrorChain.crossings(e, classifiers=classifiers)
    for crossing in crossings:
        logger.warning(
            "Domain crossing detected",
            extra=crossing.to_log_extra()
        )
```

## Logging Integration

Chain links and crossings are designed for structured logging:

```python
import logging
from domain_errors import ErrorChain, DomainError

logger = logging.getLogger(__name__)

class APIError(DomainError):
    code = "api_error"
    domain = "api"
    http_status = 502

try:
    result = fetch_from_external_api()
except TimeoutError as e:
    api_error = ErrorChain.wrap(
        e,
        as_=APIError,
        message="External API did not respond in time",
        endpoint="/users",
        timeout_seconds=30
    )
    
    # Log the full chain
    links = ErrorChain.history(api_error, classifiers=())
    for link in links:
        logger.error("Exception chain", extra=link.to_log_extra())
    
    # Log domain crossings
    crossings = ErrorChain.crossings(api_error)
    for crossing in crossings:
        logger.warning("Domain boundary crossed", extra=crossing.to_log_extra())
    
    raise api_error from e
```

## Usage Example

A complete example with wrapping, history, and crossings:

```python
from domain_errors import DomainError, ErrorChain

class DatabaseError(DomainError):
    domain = "database"
    code = "db_error"
    http_status = 503
    retryable = True

class APIError(DomainError):
    domain = "api"
    code = "api_error"
    http_status = 502

def fetch_user(user_id: str):
    try:
        return db.query("SELECT * FROM users WHERE id = $1", user_id)
    except Exception as e:
        raise ErrorChain.wrap(
            e,
            as_=DatabaseError,
            message=f"Failed to fetch user {user_id}",
            user_id=user_id
        ) from e

def get_user_via_api(user_id: str):
    try:
        return fetch_user(user_id)
    except DatabaseError as e:
        raise ErrorChain.wrap(
            e,
            as_=APIError,
            message=f"Could not retrieve user {user_id}",
            user_id=user_id
        ) from e

def handle_request(request):
    try:
        user = get_user_via_api(request.params["user_id"])
        return {"status": 200, "data": user}
    except DomainError as err:
        # Inspect the full chain
        history = ErrorChain.history(err)
        for link in history:
            logger.error("Error in chain", extra=link.to_log_extra())
        
        # Return API response
        return {
            "status": err.http_status,
            "code": err.code,
            "message": err.message
        }
```

## Design Notes

- **Cycle detection:** If the same exception object appears twice in the chain, the walk stops to prevent infinite loops.
- **Context preservation:** Each DomainError's context is preserved as-is in its link; no context merging or flattening.
- **Domain resolution cascade:** For each exception, domains are resolved in order: classvar -> first matching classifier -> fallback to `"python"`.
- **Immutable logging:** `LinkLogExtra` and `CrossingLogExtra` are frozen dataclasses, suitable for JSON serialization and immutable audit trails.

## See Also

- **DomainError Base Reference:** `docs/apps/domain_error.md`
- **Architecture:** `docs/apps/diagrams.md`
