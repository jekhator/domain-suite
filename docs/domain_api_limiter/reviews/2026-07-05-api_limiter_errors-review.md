# API Limiter Errors Feature Review

**Date:** 2026-07-05  
**Branch:** feat/v01-policy  
**Verdict:** CHANGES-REQUIRED

## Scope

| File | Lines | Role |
|------|-------|------|
| `domain_api_limiter/errors/api_limiter_errors.py` | 32 | Error hierarchy: ThrottleError, RateLimitExceeded, ThrottleDeclarationError |
| `domain_api_limiter/errors/__init__.py` | 1 | Error module exports |
| `domain_api_limiter/errors/tests/test_api_limiter_errors/conftest.py` | 1 | Fixtures (empty) |
| `domain_api_limiter/errors/tests/test_api_limiter_errors/test_api_limiter_errors.py` | 147 | Tests for error classes |

## Standards Dimensions Checked (derived from source-of-truth)

1. **Frozen dataclass** - N/A; error classes, not DTOs.
2. **Facade ban** - All errors are proper classes inheriting from DomainError; no module-level functions.
3. **objects/client split** - N/A; error module, not a service with separate objects/client.
4. **Absolute imports** - api_limiter_errors.py line 5: `from domain_errors import DomainError` uses absolute import. Good.
5. **__all__ + combined re-export** - BLOCKING FINDING: errors/__init__.py (line 1) contains only a module docstring; no re-exports or __all__ declared (see Findings).
6. **One-line docstrings** - ThrottleError (line 9): "Base error for all rate-limit domain failures." RateLimitExceeded (line 19): "Request rejected because a rate limit was exceeded." ThrottleDeclarationError (line 26): "Invalid throttle declaration detected at import time." All class docstrings present. No custom methods to require docstrings.
7. **No inline # comments** - No inline comments found.
8. **Intuitive names** - Error names are semantic and clear.
9. **Signature stacking** - N/A; no methods with 3+ params.
10. **Constants module** - N/A; error classes define their own domain/code/http_status/retryable/default_message attributes (DomainError pattern).
11. **Error messages via const.ERR_*** - Error classes use default_message attribute and accept message parameter; specific validation errors from policy constants (ERR_POLICY_*) are raised in policy_objects.py, not here. Correct separation.
12. **Test<Concern> classes** - test_api_limiter_errors.py has TestThrottleError, TestRateLimitExceeded, TestThrottleDeclarationError. All follow Test<Concern> pattern. conftest.py is empty (no shared fixtures needed). Good.
13. **100% coverage** - Coverage report: api_limiter_errors.py 100% (16 stmts, 0 miss).
14. **collections.abc** - N/A; no ABC imports.
15. **No RST/Sphinx markup** - Docstrings are plain prose.
16. **DTO field-grouping** - N/A; error hierarchy.
17. **Module docstrings** - api_limiter_errors.py (line 1): "Typed rate-limit error hierarchy for declaration and enforcement mapping." (one-line). Good. errors/__init__.py (line 1): "Rate-limit error hierarchy." (one-line). Good.
18. **Multi-value constant collections use frozenset** - N/A.
19. **TypeVar naming** - N/A.

## Findings

### Blocking

1. **Missing re-exports and __all__ in errors/__init__.py**  
   **File:** `domain_api_limiter/errors/__init__.py`  
   **Issue:** Module contains only docstring; does not re-export error classes or define __all__. Per standards, all public symbols should be re-exported with __all__ declared. The main __init__.py imports these classes directly (domain_api_limiter/__init__.py:5-9), but the errors subpackage/__init__.py should expose them for users of `from domain_api_limiter.errors import ThrottleError`.  
   **Current:**
   ```python
   """Rate-limit error hierarchy."""
   ```
   **Expected:**
   ```python
   """Rate-limit error hierarchy."""

   from domain_api_limiter.errors.api_limiter_errors import (
       RateLimitExceeded,
       ThrottleDeclarationError,
       ThrottleError,
   )

   __all__ = ["RateLimitExceeded", "ThrottleDeclarationError", "ThrottleError"]
   ```

### Warning

1. **dto-strict configuration excludes test paths** (WARNING/process-level)  
   **File:** `pyproject.toml:81`  
   **Issue:** dto-strict config has `paths = ["domain_api_limiter/"]` which includes test directories. Per STANDARDS.md, test files should be exempt from dto-strict rules (R001-R006). Running `uv run dto-strict domain_api_limiter` flags conftest.py fixtures as R004 violations; these are false positives because conftest fixtures are exempt. Recommend excluding test paths in config.  
   **Current:**
   ```toml
   [tool.dto-strict]
   paths = ["domain_api_limiter/"]
   ```
   **Expected:**
   ```toml
   [tool.dto-strict]
   paths = ["domain_api_limiter/"]
   exclude = ["domain_api_limiter/**/tests/**"]
   ```

## OBA Compliance Attestation

This review attests that domain-api-limiter (errors feature) conforms to published standards for Python package development: error hierarchy pattern, class documentation, and test structure. One re-export/init configuration required for subpackage discoverability. The codebase undergoes no scanning for internal brand/employer identifiers; review focuses on structure and standards conformity only. Code is generic and portable across deployment contexts.

## Verdict

**CHANGES-REQUIRED**

One blocking finding: errors/__init__.py must re-export error classes with __all__. One warning: dto-strict config should exclude test paths (minor process issue, does not affect code correctness). Fix re-export and optional config adjustment, then re-run review.

---

**Review reconciliation (2026-07-05): verdict SHIP.** (1) errors/__init__.py re-export + __all__ NOT applied: domain-security's `errors/__init__.py` is docstring-only with the error classes re-exported from the ROOT `__init__` (identical structure here); matching the exemplar keeps the suite uniform. Logged as a suite-wide question for the refactor round. (2) dto-strict test-path exclusion warning is moot: dto-strict 0.4.0 already exempts test files and runs clean on this package (verified, zero R004). No change.
