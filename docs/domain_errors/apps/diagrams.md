# Diagrams

> **Location:** `domain-errors/docs/apps/diagrams.md`
> **Status:** Design locked; implementation in progress.

## Error Class Hierarchy & Chaining

```
domain_errors/domains/domain_error/domain_error.py
=======================================================================
[EXCEPTION]

+- DomainError(Exception) ------------------------------------------+
|   @classvar contract:                                             |
|     code: str = "domain_error"                                    |
|     http_status: int = 500                                        |
|     retryable: bool = False                                       |
|     default_message: str                                          |
|     domain: str = "application"                                   |
|                                                                   |
|   Instance state:                                                 |
|     message: str                                                  |
|     context: dict[str, Any]                                       |
|                                                                   |
|   [mth] __init__(self, message: str | None = None, **context)   |
|         -> None                                                    |
|         Initialize exception with optional message override and   |
|         arbitrary context kwargs                                 |
|                                                                   |
|   Base exception class for domain-specific errors in consumer     |
|   projects. domain classvar is open taxonomy; consumers declare   |
|   their own like "cloud", "billing", "network", etc.             |
`-------------------------------------------------------------------+
```

## Error Chaining Service

```
domain_errors/services/chain/chain_objects.py
=======================================================================

+- [ENUM] ChainVia(StrEnum) ----------------------------------------+
|   ROOT = "root"       (exception chain started here)              |
|   CAUSE = "cause"     (linked via __cause__ per PEP 3134)        |
|   CONTEXT = "context" (linked via __context__ per PEP 3134)      |
|                                                                   |
|   How a link entered the chain                                   |
`-------------------------------------------------------------------+


+- [PROTOCOL] DomainClassifier -------------------------------------+
|   [mth] classify(err: BaseException) -> str | None                |
|         Inspect exception and return its domain string or None    |
|         when this classifier does not recognize the family.       |
|         Adapter's verdict; composable.                            |
|                                                                   |
|   Adapter model: one classifier per foreign error family          |
`-------------------------------------------------------------------+


+- [FROZEN] ChainLink ----------------------------------------------+
|   type_name: str                                                  |
|   message: str                                                    |
|   code: str | None                                                |
|   domain: str                                                     |
|   via: ChainVia                                                   |
|                                                                   |
|   [mth] to_log_extra(self) -> dict[str, str | None]              |
|         Convert this link to logging extra dict for structured   |
|         logging backends                                         |
|                                                                   |
|   Immutable causal link in an exception chain; domain and via    |
|   enable cross-domain causation tracking                         |
`-------------------------------------------------------------------+


+- [FROZEN DTO] DomainCrossing ------------------------------------+
|   cause: ChainLink                                                |
|   effect: ChainLink                                               |
|                                                                   |
|   [mth] to_log_extra(self) -> dict[str, Any]                     |
|         Convert this crossing to logging extra for structured    |
|         logging; includes domain pair (cause.domain ->            |
|         effect.domain)                                           |
|                                                                   |
|   One cross-domain causation hop (cause and effect in different  |
|   domains)                                                        |
`-------------------------------------------------------------------+


domain_errors/services/chain/chain_client.py
-----------------------------------------------------------------------

TError = TypeVar("TError", bound=DomainError)

+- [SERVICE] ErrorChain (stateless) --------------------------------+
|   [static] wrap(                                                  |
|       err: BaseException,                                         |
|       *,                                                          |
|       as_: type[TError],                                          |
|       message: str | None = None,                                |
|       **context                                                   |
|     ) -> TError                                                    |
|     Wrap an exception into a typed domain error, preserving       |
|     causal chain via PEP 3134 (raise ... from err). Consumer       |
|     projects define root subclasses (e.g. class MyProjectError    |
|     (DomainError)) and per-layer subtrees; retry middleware      |
|     keys off retryable.                                           |
|                                                                   |
|   [static] history(                                               |
|       err: BaseException,                                         |
|       classifiers: tuple[DomainClassifier, ...] = ()             |
|     ) -> tuple[ChainLink, ...]                                    |
|     Extract causal chain as an immutable tuple of ChainLinks,    |
|     in order from originating exception to current. Walks __cause__|
|     first, then __context__ unless suppressed (matching Python's |
|     traceback rules). Cycle-guarded; each link is tagged via      |
|     (ROOT/CAUSE/CONTEXT). Classifiers run in order; first match  |
|     wins; missing match defaults to "application".                |
|                                                                   |
|   [static] crossings(                                             |
|       err: BaseException,                                         |
|       classifiers: tuple[DomainClassifier, ...] = ()             |
|     ) -> tuple[DomainCrossing, ...]                               |
|     Adjacent pairs of history links whose domains differ.         |
|     Models causation hops between domains (e.g. database ->        |
|     validation -> api). Use for audit/telemetry.                  |
|                                                                   |
|   Stateless utility for PEP 3134 exception chaining with domain  |
|   awareness                                                       |
`-------------------------------------------------------------------+
```

## Domain Classifiers

```
domain_errors/domains/
=======================================================================

Adapter model: one classifier module per foreign error family.
Each exports a DomainClassifier instance.

domains/python/python_client.py  (imports: from __future__ import annotations
                                    from domain_errors.domains.constants import python as const)

+- [CLASSIFIER] PythonClassifier -----------------------------------+
|   Satisfies DomainClassifier (classify(err) -> str | None).        |
|   Stateless; CLIENT-ONLY concern (no DTOs, no _objects split).      |
|                                                                   |
|   _FAMILIES: tuple[tuple[tuple[type[BaseException],...], str],...] |
|     ORDERED most-specific-first (subtype routing is load-bearing):|
|       (ConnectionError, TimeoutError)              -> const.NETWORK |
|       (FileNotFoundError, PermissionError, OSError)-> const.OS      |
|       (ValueError, KeyError, TypeError)            -> const.LOGIC   |
|       (AssertionError,)                            -> const.ASSERTION|
|                                                                   |
|   [mth] classify(self, err: BaseException) -> str | None          |
|         walk _FAMILIES in order; first isinstance match wins;     |
|         return its domain, else None                              |
|         (None -> ErrorChain._domain_of falls back to "python")    |
`-------------------------------------------------------------------+
   module export: PythonClassifier + singleton `python = PythonClassifier()`
   consumers: ErrorChain.history(err, classifiers=(python,))

   domains/constants/python.py ("...Imported as const."):
     NETWORK / OS / LOGIC / ASSERTION  (Final domain-name strings)
   Status: Fully implemented and tested in v0.1.0

domains/http/http_client.py  (imports: from __future__ import annotations
                                    from domain_errors.domains.constants import http as const)

+- [CLASSIFIER] HttpClassifier -------------------------------------+
|   Satisfies DomainClassifier (classify(err) -> str | None).        |
|   Stateless; CLIENT-ONLY (no DTOs, no _objects split).             |
|   BY-ORIGIN: maps any exception DEFINED IN an HTTP-client library  |
|   to const.HTTP. No import of the libs (string check on            |
|   type(err).__module__), so NO optional-dep machinery AND complete |
|   coverage of each lib's whole exception surface: including httpx |
|   InvalidURL / CookieConflict / StreamError, which sit OUTSIDE the |
|   httpx.HTTPError tree (a base-class catch would miss them).       |
|                                                                   |
|   _LIBRARIES: frozenset = {"httpx", "requests", "aiohttp"}         |
|     (membership set of each lib's top-level package name)          |
|                                                                   |
|   [mth] classify(self, err: BaseException) -> str | None          |
|         const.HTTP if type(err).__module__.split(".")[0] in        |
|         _LIBRARIES, else None (specific exception preserved on     |
|         ChainLink.type_name)                                       |
`-------------------------------------------------------------------+
   module export: HttpClassifier + singleton `http = HttpClassifier()`
   consumers: ErrorChain.history(err, classifiers=(http,))

   domains/constants/http.py ("...Imported as const."):  HTTP = "http"  (single Final)
   NO runtime dep on httpx/requests/aiohttp (module-name check only); libs in dev for tests.
   Status: Fully implemented and tested in v0.1.0

domains/cloud/cloud_client.py  (imports: from __future__ import annotations
                                    from domain_errors.domains.constants import cloud as const)

+- [CLASSIFIER] CloudClassifier ------------------------------------+
|   Satisfies DomainClassifier (classify(err) -> str | None).        |
|   Stateless; CLIENT-ONLY (no DTOs, no _objects split).             |
|   BY-ORIGIN (same mechanism as http): maps any exception defined   |
|   in an AWS-SDK library to const.CLOUD via type(err).__module__.   |
|   No import of the libs (string check), no runtime dep, complete   |
|   coverage of the botocore/boto3 exception surface.               |
|                                                                   |
|   _FAMILIES via const.CLOUD_LIBRARIES: frozenset =                 |
|     {"botocore", "boto3"}  (top-level package names; membership)   |
|                                                                   |
|   [mth] classify(self, err: BaseException) -> str | None          |
|         const.CLOUD if type(err).__module__.split(".")[0] in       |
|         const.CLOUD_LIBRARIES, else None                          |
`-------------------------------------------------------------------+
   module export: CloudClassifier + singleton `cloud = CloudClassifier()`
   consumers: ErrorChain.history(err, classifiers=(cloud,))

   domains/constants/cloud.py ("...Imported as const."):
     CLOUD = "cloud"  +  CLOUD_LIBRARIES = frozenset({"botocore","boto3"})
   NO runtime dep on botocore/boto3 (module-name check only); libs in dev for tests.
   Status: Fully implemented and tested in v0.1.0
```

## Public API

```
domain_errors/__init__.py
=======================================================================

Exports:
  ChainLink             <- immutable causal chain link
  ChainVia              <- enum for chain entry mode (ROOT/CAUSE/CONTEXT)
  DomainClassifier      <- protocol for exception family adapters
  DomainCrossing        <- frozen DTO for cross-domain causation hops
  DomainError           <- base exception class
  ErrorChain            <- stateless service for wrapping/walking chains
  WrapErrorsClient      <- decorator config holder + factory
  wrap_errors           <- @wrap_errors decorator (WrapErrorsClient.for_target)
  __version__           <- package version string

Usage pattern (consumer projects):

  # 1. Define root subclass in your project
  class MyProjectError(DomainError):
      domain = "my_project"

  # 2. Per-layer subtrees (e.g. API, domain, data)
  class ApiError(MyProjectError):
      domain = "api"

  class ValidationError(ApiError):
      code = "validation_error"
      http_status = 400
      retryable = False

  # 3. Raise with chaining
  try:
      upstream_call()
  except ValueError as err:
      raise ErrorChain.wrap(err, as_=ValidationError, user_input=value) from err

  # 4. Access history in error handler
  from domain_errors.domains.python import python
  history = ErrorChain.history(exc, classifiers=(python,))  # tuple[ChainLink, ...]
```
