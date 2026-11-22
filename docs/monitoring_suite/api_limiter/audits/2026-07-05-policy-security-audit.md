# Security Audit: Policy (ThrottlePolicy, RateLimit, TierRate)

**Date:** 2026-07-05  
**Feature:** `monitoring_suite.api_limiter.services.policy`  
**Scope:** Policy value objects and introspection  

## Summary

The policy module declares immutable throttle constraints (scope, rate, tier overrides) as frozen dataclasses with import-time validation. All malformed inputs fail fast with typed errors. The module does not enforce limits, count requests, or store state. Verdict: **PASS**.

---

## Declaration Integrity: Import-Time Validation

**Requirement:** Throttle rates and policies are frozen value objects validated at declaration time (import time); malformed rates, non-positive counts, empty scope, and duplicate tiers all fail fast with `ThrottleDeclarationError` rather than silently at runtime.

### Finding: PASS

**Evidence:**

1. **RateLimit non-positive request rejection** (policy_objects.py:29-35)
   ```python
   @dataclass(frozen=True, slots=True)
   class RateLimit:
       requests: int
       period: Period

       def __post_init__(self) -> None:
           if self.requests <= 0:
               raise ThrottleDeclarationError(
                   message=const.ERR_POLICY_REQUESTS_NOT_POSITIVE,
                   requests=self.requests,
               )
   ```
   - Raises `ThrottleDeclarationError` (500, non-retryable) at object construction.
   - Test confirms: `test_direct_construction_zero_requests`, `test_direct_construction_negative_requests` (test_policy_objects.py:120-136).

2. **RateLimit.from_rate format validation** (policy_objects.py:38-54)
   ```python
   @classmethod
   def from_rate(cls, rate: str) -> Self:
       head, separator, tail = rate.partition("/")
       if not separator or not head.isdigit():
           raise ThrottleDeclarationError(
               message=const.ERR_POLICY_RATE_FORMAT,
               rate=rate,
           )
       try:
           period = Period(tail)
       except ValueError as error:
           raise ThrottleDeclarationError(
               message=const.ERR_POLICY_UNKNOWN_PERIOD,
               rate=rate,
               period=tail,
           ) from error
   ```
   - Rejects malformed rate strings (missing `/`, non-digit head, unknown period).
   - Test confirms: `test_from_rate_missing_slash`, `test_from_rate_non_digit_head`, `test_from_rate_unknown_period` (test_policy_objects.py:82-109).

3. **TierRate empty tier label rejection** (policy_objects.py:81-84)
   ```python
   @dataclass(frozen=True, slots=True)
   class TierRate:
       tier: str
       rate: RateLimit

       def __post_init__(self) -> None:
           if not self.tier:
               raise ThrottleDeclarationError(message=const.ERR_POLICY_EMPTY_TIER)
   ```
   - Raises at construction; no empty string tiers allowed.
   - Test confirms: `test_empty_tier_label_rejected` (test_policy_objects.py:199-205).

4. **ThrottlePolicy empty scope rejection** (policy_objects.py:95-104)
   ```python
   @dataclass(frozen=True, slots=True)
   class ThrottlePolicy:
       scope: str
       rate: RateLimit
       tier_rates: tuple[TierRate, ...] = ()

       def __post_init__(self) -> None:
           if not self.scope:
               raise ThrottleDeclarationError(message=const.ERR_POLICY_EMPTY_SCOPE)
           tiers = [tier_rate.tier for tier_rate in self.tier_rates]
           if len(tiers) != len(set(tiers)):
               raise ThrottleDeclarationError(
                   message=const.ERR_POLICY_DUPLICATE_TIERS,
                   scope=self.scope,
               )
   ```
   - Empty scope string rejected.
   - Duplicate tier labels detected and rejected (set cardinality check).
   - Test confirms: `test_empty_scope_rejected`, `test_duplicate_tier_labels_rejected` (test_policy_objects.py:242-268).

---

## Non-Enforcement Posture: Declaration Only

**Requirement:** This package declares only; it never enforces, counts, stores, or bypasses throttling. The consuming framework's vetted throttling implementation handles enforcement.

### Finding: PASS

**Evidence:**

1. **No counter or state storage:** RateLimit, TierRate, ThrottlePolicy are pure value objects with no mutable fields. No incrementing counters, no request tracking, no in-memory caches.
   - File: policy_objects.py (entire module is DTO-style read-only attributes).

2. **No enforcement logic:** PolicyRegistry reads policies only; no invocation, no counting, no bypass checks.
   - File: policy_client.py:15-28
   ```python
   def policy_of(self, target: Callable[..., object]) -> objs.ThrottlePolicy | None:
       """Return the policy declared on the target, or None."""
       policy = getattr(target, const.THROTTLE_POLICY_ATTR, None)
       return policy if isinstance(policy, objs.ThrottlePolicy) else None

   def collect(self, container: type | ModuleType) -> tuple[objs.ThrottlePolicy, ...]:
       """Return the policies declared on a class or module's members, in definition order."""
       policies = []
       for member in vars(container).values():
           if callable(member):
               policy = self.policy_of(member)
               if policy is not None:
                   policies.append(policy)
       return tuple(policies)
   ```
   - `policy_of`: retrieves and type-checks only.
   - `collect`: introspects only; no enforcement surface.

3. **No I/O or side effects:** No HTTP calls, database writes, Redis increments, or credential handling. All methods are pure functions or static constructors.

---

## Declaration Attribute Hygiene: Namespaced Constant

**Requirement:** The throttled decorator attaches policy via a single namespaced attribute constant (`__throttle_policy__`). PolicyRegistry reads only that attribute and type-checks it is a ThrottlePolicy; arbitrary attributes cannot masquerade as policies.

### Finding: PASS

**Evidence:**

1. **Constant definition** (services/constants/policy.py:9)
   ```python
   THROTTLE_POLICY_ATTR: Final = "__throttle_policy__"
   ```
   - Prefixed with `__` (dunder) to discourage accidental collision.
   - Marked `Final` to prevent reassignment.

2. **Decorator attachment** (decorators/throttled/throttled_client.py:34-36)
   ```python
   def declare(func: Decorated) -> Decorated:
       setattr(func, const.THROTTLE_POLICY_ATTR, policy)
       return func
   ```
   - Only location where policy is attached; uses constant exclusively.

3. **Registry type guard** (services/policy/policy_client.py:15-18)
   ```python
   def policy_of(self, target: Callable[..., object]) -> objs.ThrottlePolicy | None:
       policy = getattr(target, const.THROTTLE_POLICY_ATTR, None)
       return policy if isinstance(policy, objs.ThrottlePolicy) else None
   ```
   - Reads from constant name only.
   - Type-checks `isinstance(policy, objs.ThrottlePolicy)` before return; non-ThrottlePolicy attributes return None.
   - Test confirms: `test_policy_of_returns_none_for_non_policy_attribute`, `test_policy_of_returns_none_for_dict_attribute` (test_policy_client.py:44-68).

---

## Error-Content Review: Safe Metadata Only

**Requirement:** Raised errors carry safe metadata only (scope names, rate strings, counts), no secrets or personal data.

### Finding: PASS

**Evidence:**

1. **RateLimit validation error contexts** (policy_objects.py:32-53)
   ```python
   raise ThrottleDeclarationError(
       message=const.ERR_POLICY_REQUESTS_NOT_POSITIVE,
       requests=self.requests,
   )
   ```
   - Context: `{"requests": <int count>}` only.

   ```python
   raise ThrottleDeclarationError(
       message=const.ERR_POLICY_RATE_FORMAT,
       rate=rate,
   )
   ```
   - Context: `{"rate": <string like "100/hour">}` only.

2. **TierRate and ThrottlePolicy error contexts** (policy_objects.py:84, 101-104)
   ```python
   raise ThrottleDeclarationError(message=const.ERR_POLICY_EMPTY_TIER)
   raise ThrottleDeclarationError(
       message=const.ERR_POLICY_DUPLICATE_TIERS,
       scope=self.scope,
   )
   ```
   - Scope is a string label (e.g., "api.users.list"), not user PII or secrets.

3. **No credential or personal data in error messages:**
   - Constants (policy.py:14-19) are generic strings: "rate requests must be positive", "unknown rate period", etc.
   - No timestamps, user identifiers, request IDs, or tokens appear in error context.
   - Tests verify context structure (test_policy_objects.py:89-108, test_api_limiter_errors.py:136-146).

---

## Immutability: Frozen + Slots

**Requirement:** Frozen and slots dataclasses; tier_rates is a tuple (no post-construction mutation).

### Finding: PASS

**Evidence:**

1. **All value objects frozen** (policy_objects.py:22, 74-75, 87-88)
   ```python
   @dataclass(frozen=True, slots=True)
   class RateLimit: ...

   @dataclass(frozen=True, slots=True)
   class TierRate: ...

   @dataclass(frozen=True, slots=True)
   class ThrottlePolicy: ...
   ```
   - `frozen=True` prevents attribute reassignment after construction.
   - `slots=True` prevents dynamic attribute addition.

2. **tier_rates is a tuple** (policy_objects.py:93)
   ```python
   tier_rates: tuple[TierRate, ...] = ()
   ```
   - Tuple is immutable; cannot append, remove, or replace elements.
   - Default factory unnecessary (immutable by nature).

3. **Test confirms immutability** (test_policy_objects.py:182-186, 207-213, 335-342)
   ```python
   def test_frozen_prevents_modification(self) -> None:
       rate = RateLimit(requests=100, period=Period.HOUR)
       with pytest.raises(FrozenInstanceError):
           rate.requests = 200  # type: ignore
   ```
   - Attempting to modify frozen object raises `FrozenInstanceError`.

---

## Dependency Surface: Single monitoring_suite.errors Dependency

**Requirement:** Single runtime dependency (monitoring_suite.errors); no homegrown or unsafe dependencies; stdlib only for mechanics.

### Finding: PASS

**Evidence:**

1. **Single domain import** (api_limiter_errors.py:5)
   ```python
   from monitoring_suite.errors import DomainError
   ```
   - Only external runtime dependency.

2. **Policy module uses only stdlib + monitoring_suite.errors** (policy_objects.py:5-10)
   ```python
   from dataclasses import dataclass
   from enum import StrEnum
   from typing import Self

   from monitoring_suite.api_limiter.errors.api_limiter_errors import ThrottleDeclarationError
   from monitoring_suite.api_limiter.services.constants import policy as const
   ```
   - `dataclasses`, `enum`, `typing` are all Python stdlib.
   - Only internal imports (errors, constants).

3. **PolicyRegistry uses only stdlib + local classes** (policy_client.py:5-9)
   ```python
   from collections.abc import Callable, Mapping
   from types import ModuleType

   from monitoring_suite.api_limiter.services.constants import policy as const
   from monitoring_suite.api_limiter.services.policy.policy_objects import ...
   ```
   - `collections.abc`, `types` are stdlib.

4. **pyproject.toml confirms single runtime dep** (verified via build manifest).
   - monitoring_suite.errors is the sole published dependency for this package.

---

## Verdict

**Status: PASS**

All core security properties are satisfied:
- Declaration integrity enforced at import time via frozen dataclasses and `__post_init__` validation.
- Non-enforcement posture strictly observed: no counters, no enforcement logic, no I/O.
- Declaration attribute hygiene: `__throttle_policy__` constant is the single attachment point; PolicyRegistry type-guards via `isinstance`.
- Error metadata is safe: scope names, rate strings, counts only; no secrets or personal data.
- Immutability via `frozen=True`, `slots=True`, and tuple fields.
- Dependency surface minimal: monitoring_suite.errors only; stdlib for all mechanics.

No findings. Package ready for use as a declaration-only toolkit.
