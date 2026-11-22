# monitoring_suite.errors. HTTP Classifier

> **Location:** `monitoring_suite/errors/docs/apps/http.md`
> **Status:** Living reference. HTTP classifier fully implemented in v0.1.0+.
> **Code location:** `monitoring_suite/errors/domains/http/http_client.py`
> **Constants:** `monitoring_suite/errors/domains/constants/http.py`
> **Sibling docs:** `docs/apps/domain_error.md`, `docs/apps/chain.md`, `docs/apps/diagrams.md`

## Purpose

`HttpClassifier` maps HTTP-client exception families to a coarse semantic domain. It adapts foreign (non-DomainError) exceptions from httpx, requests, and aiohttp so they can be classified alongside domain-specific errors in exception chains, enabling unified tracing when HTTP exceptions cross domain boundaries (e.g., a connection error in the network layer propagates to an API layer).

## Core Design

The classifier is **stateless** and **composable**. It satisfies the `DomainClassifier` protocol: given a caught exception, it returns the exception's domain string or None.

```python
class DomainClassifier(Protocol):
    def classify(self, err: BaseException) -> str | None:
        """Return the error's domain, or None when it is not this family."""
```

## The HttpClassifier Class

### Instance

```python
from monitoring_suite.errors.domains.http import http

http: HttpClassifier = HttpClassifier()
```

The module exports a singleton `http` instance; there is no need to instantiate HttpClassifier yourself.

### By-Origin Design

The classifier identifies exceptions by their **origin module**, not by base class. This strategy covers each HTTP-client library's entire exception surface, including exceptions that sit outside the main error hierarchy.

For example, httpx exports not just `HTTPError` and its subclasses, but also standalone exceptions like `InvalidURL`, `CookieConflict`, and `StreamError` (nested in the httpx namespace but not subclasses of `HTTPError`). A base-class catch would miss them. By checking `type(err).__module__`, the classifier captures all of them.

```python
_LIBRARIES: frozenset = {"httpx", "requests", "aiohttp"}
```

The classifier maintains a frozenset of top-level package names for the recognized HTTP-client libraries.

### No Runtime Dependency

The classifier imports **none** of the HTTP-client libraries. It inspects exception objects by name only (checking the module path string). This means:

- No optional-dependency machinery needed; all three libraries (httpx, requests, aiohttp) are dev-only for tests.
- The classifier is robust to library version changes and alternative async HTTP clients (as long as they are at the same module level).

## The classify() Method

```python
def classify(self, err: BaseException) -> str | None:
    """Return err's HTTP-client domain, or None when no library match."""
```

### Parameters

- `err`: any caught exception

### Returns

The domain string `"http"` if the exception originated in one of the recognized HTTP-client libraries (httpx, requests, aiohttp), or `None` if the exception's module is not recognized.

### Behavior

Extracts the top-level package name from `type(err).__module__` (the first element when split on `.`). If that package is in `_LIBRARIES`, returns `const.HTTP`. Otherwise, returns `None`.

When returned from `ErrorChain.history()` or `ErrorChain.crossings()`, a `None` result falls back to the fallback domain `"application"`.

### Example

```python
from monitoring_suite.errors.domains.http import http
import httpx

# Matches httpx exception -> "http"
result = http.classify(httpx.InvalidURL("https://invalid"))
assert result == "http"

# Matches requests exception -> "http"
import requests
result = http.classify(requests.ConnectionError("Failed to connect"))
assert result == "http"

# No match
result = http.classify(ValueError("Invalid input"))
assert result is None
```

## Usage with ErrorChain

Pass the `http` classifier to `history()` or `crossings()` to resolve domains for HTTP-client exceptions in the exception chain:

```python
from monitoring_suite.errors import ErrorChain, DomainError
from monitoring_suite.errors.domains.http import http

class APIError(DomainError):
    code = "api_error"
    domain = "api"
    http_status = 502

try:
    result = await httpx.AsyncClient().get("https://external.api")
except httpx.ConnectError as e:
    api_error = ErrorChain.wrap(
        e,
        as_=APIError,
        message="External API unreachable"
    )
    
    # Walk the chain and classify foreign exceptions
    links = ErrorChain.history(api_error, classifiers=(http,))
    for link in links:
        print(f"{link.type_name} ({link.domain}): {link.message}")
        # Output:
        # APIError (api): External API unreachable
        # ConnectError (http): Failed to connect
    
    raise api_error from e
```

## Composing Multiple Classifiers

Classifiers compose; pass multiple to the same call. The first classifier whose verdict is not `None` wins:

```python
from monitoring_suite.errors import ErrorChain
from monitoring_suite.errors.domains.python import python
from monitoring_suite.errors.domains.http import http

try:
    result = await process()
except Exception as e:
    # Try python first, then http, then other classifiers
    links = ErrorChain.history(e, classifiers=(python, http))
    for link in links:
        logger.error("Exception", extra=link.to_log_extra())
```

## Design Notes

- **Singleton export:** Instantiate once per module as `http = HttpClassifier()`. Stateless, safe to share.
- **By-origin not by-base-class:** Inspects `type(err).__module__` to catch the entire library surface, not just the main exception tree.
- **No runtime imports:** All three libraries are development dependencies for testing; they are never imported by the classifier itself.
- **None means not recognized:** If `classify()` returns `None`, `ErrorChain._domain_of()` falls back to the sentinel domain `"application"`.
- **No exceptions raised:** The classifier never raises; all return paths are valid.

## See Also

- **ErrorChain:** `docs/apps/chain.md`: how to use classifiers with history/crossings
- **DomainError Base:** `docs/apps/domain_error.md`: how to define domain-specific errors
- **Architecture:** `docs/apps/diagrams.md`: system diagram with classifier placement
