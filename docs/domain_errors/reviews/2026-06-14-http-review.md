# HTTP Classifier Review

**Date:** 2026-06-14  
**Feature:** http (domains/http)  
**Scope:** HTTP-client exception classification by origin, frozenset-based library matching, module-name handling

## Findings

### Classification Correctness

**Sound.** HttpClassifier classifies exceptions by their originating library (httpx, requests, aiohttp) using a module-origin check. The classify() method extracts the top-level package name (`type(err).__module__.split(".")[0]`) and tests membership in HTTP_LIBRARIES. This approach is correct because exceptions from HTTP-client libraries can have diverse base classes (some subclass HTTPError, others subclass RuntimeError or ValueError) and non-deterministic inheritance trees across library versions. Origin-based classification sidesteps all of that: if the exception came from httpx, it's HTTP, regardless of its base class. The method correctly guards against exceptions with no module (builtins) by default:they will not match any top-level package name in HTTP_LIBRARIES.

### Frozenset vs. Tuple Rationale

**Correct choice.** HTTP_LIBRARIES is a frozenset, not a tuple, and this is the right decision. Order does not matter: the check is membership (`in`), not iteration. A frozenset provides O(1) lookup and makes it clear to readers that order is irrelevant. Using a tuple would suggest order-dependent matching (as in python's _FAMILIES), which would be incorrect here.

### Docstrings and Naming

**Standards compliant.** The class docstring is one-line ("Classify httpx, requests, and aiohttp exceptions into the http domain."), the classify method docstring is one-line ("Return const.HTTP when err originates in an HTTP-client library, else None."), and the module docstring is one-line ("HTTP exception-family domain classifier."). The HTTP_LIBRARIES constant has a one-line docstring above it. No inline comments clutter the code.

### Constants

**Standards compliant.** HTTP_LIBRARIES is imported as `from domain_errors.domains.constants import http as const`, and both HTTP and HTTP_LIBRARIES are correctly scoped to the constant module. No string literals or hardcoded library names in the classifier.

### Imports

**Standards compliant.** Combined-absolute imports; no relative imports or from-future annotations except the standard `from __future__ import annotations`.

### Singleton Export

**Correct.** The module exports `http = HttpClassifier()` at the bottom, providing a stateless singleton. Tests verify instantiation and correct behavior.

### Test Coverage

**Complete: 100%.** Tests cover httpx (HTTPError, ConnectTimeout, ConnectError, HTTPStatusError, TooManyRedirects, InvalidURL, CookieConflict, StreamError, StreamConsumed, ResponseNotRead), requests (RequestException, InvalidURL), aiohttp (ClientError), unrecognized exceptions (ValueError, RuntimeError, custom), singleton instantiation, and stateless behavior. Test organization uses descriptive classes and method names. Tests confirm the library-name check works for exceptions both in and outside the main HTTPError hierarchy.

### Residual Observations

- No type: ignore comments are needed; the code is fully typed.
- The module-name split is safe: all exception objects have a __module__ attribute.
- No dataclass or value-object construction; HttpClassifier is stateless.

## Verdict

HTTP classifier is correct, standards-conformant, and ready. Origin-based classification is the right model for library exceptions; frozenset membership test is idiomatic; test coverage is complete. No defects or divergences.
