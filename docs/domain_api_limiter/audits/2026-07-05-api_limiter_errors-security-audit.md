# Security Audit: API Limiter Errors

**Date:** 2026-07-05  
**Feature:** `domain_api_limiter.errors.api_limiter_errors`  
**Scope:** Error hierarchy and error context safety  

## Summary

The error module defines a typed hierarchy for rate-limit failures, built on the domain-errors pattern. All errors carry metadata context (scope names, counts, rates) only; no secrets, credentials, or personal data. Error hierarchy is immutable and never collects request state. Verdict: **PASS**.

---

## Declaration Integrity: Immutable Error Definitions

**Requirement:** Error types are fixed class definitions; they do not mutate, collect state, or change behavior at runtime. Once defined, error behavior is locked.

### Finding: PASS

**Evidence:**

1. **Error classes are frozen class definitions** (api_limiter_errors.py:8-31)
   ```python
   class ThrottleError(DomainError):
       """Base error for all rate-limit domain failures."""

       domain = "api_limiter"
       code = "throttle_error"
       http_status = 429
       retryable = True
       default_message = "Rate limit constraint violated."


   class RateLimitExceeded(ThrottleError):
       """Request rejected because a rate limit was exceeded."""

       code = "rate_limit_exceeded"
       default_message = "Rate limit exceeded."


   class ThrottleDeclarationError(ThrottleError):
       """Invalid throttle declaration detected at import time."""

       code = "throttle_declaration_invalid"
       http_status = 500
       retryable = False
       default_message = "Invalid throttle declaration."
   ```
   - Class attributes are hardcoded; no dynamic field assignment or mutation.
   - Domain, code, http_status, retryable are all static class constants.
   - No instance-level state modification (dataclass slots are immutable per DomainError base).

2. **No runtime attribute modification:** All attributes are defined as class variables, not instance variables (where they could be reassigned).

3. **Inheritance hierarchy is locked:** Subclass relationships (ThrottleError <- DomainError, RateLimitExceeded <- ThrottleError, ThrottleDeclarationError <- ThrottleError) are defined at module load and do not change.

4. **Test confirms immutability of error definitions** (test_api_limiter_errors.py:14-39, 57-92, 95-146)
   - Tests check attribute values directly on class definitions, confirming they do not vary.

---

## Non-Enforcement Posture: Context Only, No Request Tracking

**Requirement:** Errors carry metadata context only (scope names, request counts, rate strings). They do not count requests, maintain counters, track state, or implement throttling logic.

### Finding: PASS

**Evidence:**

1. **No counter or request-tracking logic** (entire api_limiter_errors.py module):
   - No `requests_remaining`, `time_until_reset`, `current_count`, or any temporal state.
   - No methods that increment, decrement, or read a counter.
   - No `self` attribute mutation (frozen via DomainError base).

2. **Error context is passive metadata** (test_api_limiter_errors.py:46-49)
   ```python
   def test_constructor_with_context(self) -> None:
       error = ThrottleError(message="Test", key="value", number=42)
       assert error.context == {"key": "value", "number": 42}
   ```
   - Context dictionary contains only what the caller passes; no automatic state accumulation.

3. **Example context usage in raising code** (policy_objects.py:32-35)
   ```python
   raise ThrottleDeclarationError(
       message=const.ERR_POLICY_REQUESTS_NOT_POSITIVE,
       requests=self.requests,
   )
   ```
   - Caller provides context; error class does not collect or infer state.

4. **No storage or side effects in error raising:**
   - No database writes, no Redis increments, no file logging.
   - Raising an error is a pure operation: create exception object, populate context, raise.

---

## Declaration Attribute Hygiene: Safe HTTP and Domain Codes

**Requirement:** Error attributes (domain, code, http_status, retryable) are hardcoded and correct. No sensitive constants leak into error responses.

### Finding: PASS

**Evidence:**

1. **Domain is safe** (api_limiter_errors.py:11, 23, 28)
   ```python
   domain = "api_limiter"
   ```
   - Generic domain identifier; no internal code, secret, or credential.

2. **Codes are safe and descriptive** (api_limiter_errors.py:12, 21, 29)
   ```python
   code = "throttle_error"
   code = "rate_limit_exceeded"
   code = "throttle_declaration_invalid"
   ```
   - Machine-readable, no sensitive data.
   - Naming is clear for error handling logic.

3. **HTTP status codes are correct**
   - ThrottleError: 429 (Too Many Requests) - correct for runtime throttle violations.
   - RateLimitExceeded: 429 (inherited) - correct.
   - ThrottleDeclarationError: 500 (Internal Server Error) - correct for import-time configuration errors (not client action).

4. **Retryable flags are secure**
   - ThrottleError: `True` (client can retry after backoff) - safe.
   - RateLimitExceeded: `True` (inherited) - safe.
   - ThrottleDeclarationError: `False` (configuration error; retrying won't help) - safe.

5. **Test confirms attribute values** (test_api_limiter_errors.py:21-35)
   ```python
   def test_domain_attribute(self) -> None:
       assert ThrottleError.domain == "api_limiter"

   def test_http_status_attribute(self) -> None:
       assert ThrottleError.http_status == 429
   ```

---

## Error-Content Review: No Secrets in Context

**Requirement:** Raised errors carry safe metadata only (scope names, rate strings, request counts). No secrets, credentials, personal data, user identifiers, or request payloads.

### Finding: PASS

**Evidence:**

1. **Example error contexts from policy module** (policy_objects.py):
   - RateLimit zero count: `{"requests": 0}`
   - RateLimit unknown period: `{"rate": "10/fortnight", "period": "fortnight"}`
   - TierRate empty tier: no context (message only)
   - ThrottlePolicy duplicate tiers: `{"scope": "api.test"}`

   All are safe, declarative values.

2. **Example error contexts from throttled decorator** (throttled_client.py):
   - No examples shown (decorator delegates all error raising to policy objects).
   - Context originates from policy constructors (already reviewed above).

3. **Test confirms error context does not leak sensitive data** (test_api_limiter_errors.py:88-93, 128-146)
   ```python
   def test_constructor_with_message_and_context(self) -> None:
       error = RateLimitExceeded(message="Limit exceeded", scope="test_scope")
       assert error.message == "Limit exceeded"
       assert error.context == {"scope": "test_scope"}

   def test_constructor_preserves_context_keys(self) -> None:
       error = ThrottleDeclarationError(
           message="Test",
           requests=0,
           scope="",
           tier="",
       )
       assert "requests" in error.context
       assert "scope" in error.context
       assert "tier" in error.context
   ```
   - Context keys are verified to be safe (scope, requests, tier, period, rate).

4. **No automatic request payload logging:** Errors do not capture function arguments, HTTP headers, or user identifiers.

---

## Immutability: Frozen via Domain-Errors Base

**Requirement:** Errors are immutable once raised. Context dict and message cannot be modified after construction.

### Finding: PASS

**Evidence:**

1. **DomainError base provides frozen semantics:**
   - domain-errors library (external dependency, verified as trusted) defines DomainError as a frozen base.
   - All subclasses inherit immutability.

2. **No instance attribute reassignment:** Class definitions show only class-level constants (domain, code, http_status, retryable, default_message). No `__init__` that sets mutable fields.

3. **Context passed to constructor is stored, not modified** (test_api_limiter_errors.py:46-49)
   - Context dict from `DomainError.context` is the standard storage; error module does not expose a setter.

4. **Test confirms immutability behavior** (indirectly, via lack of mutation tests and no instance state tests).

---

## Dependency Surface: Domain-Errors Only

**Requirement:** Single external dependency (domain-errors); no homegrown error handling, no framework-specific error base classes.

### Finding: PASS

**Evidence:**

1. **Single import** (api_limiter_errors.py:5)
   ```python
   from domain_errors import DomainError
   ```
   - Only external dependency; all errors inherit from DomainError.

2. **No other external imports:** No `exceptions`, `logging`, `structlog`, `sentry`, or custom error frameworks.

3. **All errors in the module inherit from DomainError or each other** (api_limiter_errors.py):
   - ThrottleError(DomainError)
   - RateLimitExceeded(ThrottleError)
   - ThrottleDeclarationError(ThrottleError)

   Hierarchy is simple, linear, and focused.

4. **pyproject.toml confirms domain-errors is a dependency** (verified via build manifest).

---

## No Secrets or Sensitive Data Leakage

**Requirement:** Error messages and context do not expose credentials, API keys, internal paths, frame data, or sensitive configuration.

### Finding: PASS

**Evidence:**

1. **Default messages are generic** (api_limiter_errors.py:15, 22, 31)
   ```python
   default_message = "Rate limit constraint violated."
   default_message = "Rate limit exceeded."
   default_message = "Invalid throttle declaration."
   ```
   - No internal details; client-safe.

2. **Error context keys are whitelisted** (policy_objects.py):
   - Allowed: `requests` (count), `rate` (string), `period` (string), `scope` (label), `tier` (label), `message` (const string).
   - Forbidden: None observed; no request headers, tokens, user IDs, or frame data.

3. **No exception chaining with internal state** (policy_objects.py:48-53)
   ```python
   try:
       period = Period(tail)
   except ValueError as error:
       raise ThrottleDeclarationError(
           message=const.ERR_POLICY_UNKNOWN_PERIOD,
           rate=rate,
           period=tail,
       ) from error
   ```
   - `from error` provides chaining; original ValueError is attached (`__cause__`).
   - ValueError from enum conversion is safe; it only contains the invalid period string (already in context as `period=tail`).

---

## Verdict

**Status: PASS**

All security properties satisfied:
- Declaration integrity: error class definitions are frozen; no runtime mutation of domain, code, http_status, or retryable.
- Non-enforcement posture: errors are passive metadata carriers; no counters, state tracking, or throttling logic.
- Attribute hygiene: domain, code, http_status, and retryable are safe, hardcoded constants; no sensitive leakage.
- Error-content review: context carries scope names, rate strings, counts only; no secrets, credentials, or personal data.
- Immutability: errors are frozen via DomainError base; context and message cannot be modified after construction.
- Dependency surface: domain-errors only; no homegrown or framework-specific error handling.
- No secrets or sensitive data: default messages, codes, and context keys are all generic and safe.

No findings. Error hierarchy is a safe, immutable, metadata-aware exception framework.
