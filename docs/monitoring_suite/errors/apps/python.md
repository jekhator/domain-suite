# monitoring_suite.errors. Python Stdlib Classifier

> **Location:** `monitoring_suite/errors/docs/apps/python.md`
> **Status:** Living reference. Python classifier fully implemented in v0.1.0+.
> **Code location:** `monitoring_suite/errors/domains/python/python_client.py`
> **Constants:** `monitoring_suite/errors/domains/constants/python.py`
> **Sibling docs:** `docs/apps/domain_error.md`, `docs/apps/chain.md`, `docs/apps/diagrams.md`

## Purpose

`PythonClassifier` maps standard library exception families to coarse semantic domains. It adapts foreign (non-DomainError) Python exceptions so they can be classified alongside domain-specific errors in exception chains, enabling unified tracing when stdlib exceptions cross domain boundaries (e.g., a `TimeoutError` in the network layer propagates to an API layer).

## Core Design

The classifier is **stateless** and **composable**. It satisfies the `DomainClassifier` protocol: given a caught exception, it returns the exception's domain string or None.

```python
class DomainClassifier(Protocol):
    def classify(self, err: BaseException) -> str | None:
        """Return the error's domain, or None when it is not this family."""
```

## The PythonClassifier Class

### Instance

```python
from monitoring_suite.errors.domains.python import python

python: PythonClassifier = PythonClassifier()
```

The module exports a singleton `python` instance; there is no need to instantiate PythonClassifier yourself.

### Family Mapping

The classifier maintains an ordered tuple of exception families, each bound to a domain string:

```python
_FAMILIES: tuple[tuple[tuple[type[BaseException], ...], str], ...] = (
    ((ConnectionError, TimeoutError), const.NETWORK),
    ((FileNotFoundError, PermissionError, OSError), const.OS),
    ((ValueError, KeyError, TypeError), const.LOGIC),
    ((AssertionError,), const.ASSERTION),
)
```

**Ordering is load-bearing:** Families are checked most-specific-first. A subclass match stops the walk (first match wins). For example, `ConnectionError` and `TimeoutError` are checked before `OSError`, even though they are subclasses of `OSError` in the inheritance hierarchy.

### Domain Names

The classifier maps to four coarse domains:

- **`"network"`**: Network-layer exceptions: `ConnectionError`, `TimeoutError`
- **`"os"`**: Operating system and I/O exceptions: `FileNotFoundError`, `PermissionError`, `OSError` (and subclasses)
- **`"logic"`**: Logical/programming errors: `ValueError`, `KeyError`, `TypeError`
- **`"assertion"`**: Assertion failures: `AssertionError`

These constants are exported from `monitoring_suite/errors/domains/constants/python.py`:

```python
from monitoring_suite.errors.domains.constants.python import NETWORK, OS, LOGIC, ASSERTION
```

## The classify() Method

```python
def classify(self, err: BaseException) -> str | None:
    """Return err's stdlib domain, or None when no family matches."""
```

### Parameters

- `err`: any caught exception

### Returns

A domain name string (`"network"`, `"os"`, `"logic"`, `"assertion"`) if the exception is an instance of one of the recognized families, or `None` if no family matches.

### Behavior

Walks `_FAMILIES` in order. The first tuple whose exception types match (via `isinstance`) returns its domain. If no family matches, returns `None`.

When returned from `ErrorChain.history()` or `ErrorChain.crossings()`, a `None` result falls back to the fallback domain `"python"`.

### Example

```python
from monitoring_suite.errors.domains.python import python

# Matches (ConnectionError, TimeoutError) -> "network"
result = python.classify(TimeoutError("Connection timed out"))
assert result == "network"

# Matches (ValueError, KeyError, TypeError) -> "logic"
result = python.classify(ValueError("Invalid input"))
assert result == "logic"

# No match
result = python.classify(RuntimeError("Something went wrong"))
assert result is None
```

## Usage with ErrorChain

Pass the `python` classifier to `history()` or `crossings()` to resolve domains for stdlib exceptions in the exception chain:

```python
from monitoring_suite.errors import ErrorChain, DomainError
from monitoring_suite.errors.domains.python import python

class APIError(DomainError):
    code = "api_error"
    domain = "api"
    http_status = 502

try:
    result = await fetch_from_external_api()
except TimeoutError as e:
    api_error = ErrorChain.wrap(
        e,
        as_=APIError,
        message="External API did not respond in time"
    )
    
    # Walk the chain and classify foreign exceptions
    links = ErrorChain.history(api_error, classifiers=(python,))
    for link in links:
        print(f"{link.type_name} ({link.domain}): {link.message}")
        # Output:
        # APIError (api): External API did not respond in time
        # TimeoutError (network): Connection timed out
    
    raise api_error from e
```

## Composing Multiple Classifiers

Classifiers compose; pass multiple to the same call. The first classifier whose verdict is not `None` wins:

```python
from monitoring_suite.errors import ErrorChain
from monitoring_suite.errors.domains.python import python
from monitoring_suite.errors.domains.http import http  # hypothetical

try:
    result = await process()
except Exception as e:
    # Try python first, then http, then other classifiers
    links = ErrorChain.history(e, classifiers=(python, http))
    for link in links:
        logger.error("Exception", extra=link.to_log_extra())
```

## Design Notes

- **Singleton export:** Instantiate once per module as `python = PythonClassifier()`. Stateless, safe to share.
- **First match wins:** The `_FAMILIES` tuple is ordered; subclass matches must come before parent class matches.
- **None means not recognized:** If `classify()` returns `None`, `ErrorChain._domain_of()` falls back to the sentinel domain `"python"`.
- **No exceptions raised:** The classifier never raises; all return paths are valid.

## See Also

- **ErrorChain:** `docs/apps/chain.md`: how to use classifiers with history/crossings
- **DomainError Base:** `docs/apps/domain_error.md`: how to define domain-specific errors
- **Architecture:** `docs/apps/diagrams.md`: system diagram with classifier placement
