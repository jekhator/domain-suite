# Security Audit: Throttled Decorator

**Date:** 2026-07-05  
**Feature:** `monitoring_suite.api_limiter.decorators.throttled`  
**Scope:** Declaration decorator and policy attachment  

## Summary

The throttled decorator validates and attaches a ThrottlePolicy to a callable without wrapping or altering execution. Validation occurs at decoration time (import time). The decorator is a pure metadata appliance: it does not execute, count, throttle, or persist state. Verdict: **PASS**.

---

## Declaration Integrity: Decoration-Time Validation

**Requirement:** Throttle policies attached by the decorator are validated at decoration time (when the decorator is applied), not at runtime. Malformed rates, policies, and tier overrides all fail fast at module import.

### Finding: PASS

**Evidence:**

1. **Policy construction during decoration** (throttled_client.py:21-32)
   ```python
   def __call__(
       self,
       scope: str,
       rate: str,
       tiers: Mapping[str, str] | None = None,
   ) -> Callable[[Decorated], Decorated]:
       policy = ThrottlePolicy(
           scope=scope,
           rate=RateLimit.from_rate(rate),
           tier_rates=self._tier_rates(tiers),
       )

       def declare(func: Decorated) -> Decorated:
           setattr(func, const.THROTTLE_POLICY_ATTR, policy)
           return func

       return declare
   ```
   - `ThrottlePolicy()` constructor is called BEFORE the decorator factory returns.
   - `RateLimit.from_rate()` is called BEFORE `declare()` is defined.
   - All validation (`__post_init__` on RateLimit, TierRate, ThrottlePolicy) fires synchronously.
   - If any validation fails, a `ThrottleDeclarationError` is raised and the decorator aborts.

2. **Tier-rate construction at decoration time** (throttled_client.py:40-48)
   ```python
   @staticmethod
   def _tier_rates(tiers: Mapping[str, str] | None) -> tuple[TierRate, ...]:
       if not tiers:
           return ()
       return tuple(
           TierRate(tier=tier, rate=RateLimit.from_rate(rate))
           for tier, rate in tiers.items()
       )
   ```
   - Each `TierRate()` construction (tier validation) and `RateLimit.from_rate()` (rate validation) fires synchronously.
   - Duplicate tier detection (in ThrottlePolicy `__post_init__`) runs at decoration time.

3. **Test confirms decoration-time validation** (test_throttled_client.py:203-266)
   ```python
   def test_invalid_rate_raises_at_decoration(self) -> None:
       def my_function() -> None:
           pass

       with pytest.raises(
           ThrottleDeclarationError,
           match=re.escape(const.ERR_POLICY_RATE_FORMAT),
       ):
           throttled(scope="test", rate="invalid")(my_function)
   ```
   - Raises during the call to `throttled(...)`, NOT during the inner call to `(my_function)`.
   - Similar tests: `test_unknown_period_raises_at_decoration`, `test_zero_rate_raises_at_decoration`, `test_invalid_tier_rate_raises_at_decoration`, `test_empty_scope_raises_at_decoration`, `test_empty_tier_label_raises_at_decoration` all confirm import-time failures.

---

## Non-Enforcement Posture: Pure Metadata Appliance

**Requirement:** The decorator does not wrap, execute, enforce, count, or throttle. It only attaches metadata. Function behavior is unchanged.

### Finding: PASS

**Evidence:**

1. **Decorator returns the exact same function object** (test_throttled_client.py:18-31)
   ```python
   def test_decorator_returns_original_function_object(self) -> None:
       def my_function() -> None:
           pass

       original_id = id(my_function)
       decorated = throttled(scope="test", rate="100/hour")(my_function)

       assert id(decorated) == original_id
       assert decorated is my_function
   ```
   - Object identity is preserved (`is` check).
   - No wrapper function; no execution interception.

2. **Function behavior unchanged** (test_throttled_client.py:46-63)
   ```python
   def test_decorator_preserves_function_identity_with_args(self) -> None:
       def add(a: int, b: int) -> int:
           return a + b

       decorated = throttled(scope="math.add", rate="1000/second")(add)
       assert decorated(2, 3) == 5

   def test_decorator_preserves_function_name(self) -> None:
       decorated = throttled(scope="test", rate="100/hour")(original_name)
       assert decorated.__name__ == "original_name"

   def test_decorator_preserves_function_docstring(self) -> None:
       decorated = throttled(scope="test", rate="100/hour")(documented_func)
       assert decorated.__doc__ == "This is the docstring."
   ```
   - Function executes identically after decoration.
   - Name and docstring untouched (no wrapping).

3. **Implementation confirms no wrapping** (throttled_client.py:34-37)
   ```python
   def declare(func: Decorated) -> Decorated:
       setattr(func, const.THROTTLE_POLICY_ATTR, policy)
       return func
   ```
   - Only operation: `setattr()` to attach policy, then `return func`.
   - No intermediate wrapper, no try/except, no execution hooks.

4. **No counters, storage, or caching:** The entire module (throttled_client.py) contains no `self.requests`, `cache`, `redis`, `counter`, or any mutable state.

---

## Declaration Attribute Hygiene: Namespaced Constant

**Requirement:** The decorator attaches policy via a single constant (`__throttle_policy__`). The attribute is readable by PolicyRegistry; no other attributes masquerade as policies.

### Finding: PASS

**Evidence:**

1. **Policy attached via constant only** (throttled_client.py:35)
   ```python
   setattr(func, const.THROTTLE_POLICY_ATTR, policy)
   ```
   - Uses `const.THROTTLE_POLICY_ATTR` (`__throttle_policy__`) exclusively.
   - No alternative attribute names or dynamic key construction.

2. **Constant is a module-level final** (services/constants/policy.py:9)
   ```python
   THROTTLE_POLICY_ATTR: Final = "__throttle_policy__"
   ```
   - Centralized definition prevents inconsistency.

3. **PolicyRegistry type-guards the attachment** (services/policy/policy_client.py:17-18)
   ```python
   policy = getattr(target, const.THROTTLE_POLICY_ATTR, None)
   return policy if isinstance(policy, objs.ThrottlePolicy) else None
   ```
   - Even if something else writes to `__throttle_policy__`, the `isinstance()` guard rejects non-ThrottlePolicy values.
   - Test confirms: `test_policy_of_returns_none_for_non_policy_attribute` (test_policy_client.py:44-55).

---

## Error-Content Review: Safe Metadata in Context

**Requirement:** Raised errors carry safe metadata only: scope names, rate strings, tier labels, counts. No secrets, credentials, personal data, or sensitive internals.

### Finding: PASS

**Evidence:**

1. **Validation errors carry scope, rate, period, tier** (throttled_client.py:28-31)
   ```python
   policy = ThrottlePolicy(
       scope=scope,
       rate=RateLimit.from_rate(rate),
       tier_rates=self._tier_rates(tiers),
   )
   ```
   - All exceptions come from policy object constructors, which validate input.
   - Input parameters: `scope` (string label), `rate` (string like "100/hour"), `tiers` (dict of label->rate).

2. **Example error contexts from policy constructors** (policy_objects.py):
   - RateLimit: `{"requests": <count>, "rate": "100/hour", "period": "unknown"}`
   - TierRate: no additional context (empty tier raises with message only)
   - ThrottlePolicy: `{"scope": "api.users.list"}`

   All are safe, declarative metadata; no function signatures, frame data, or user request context.

3. **Tests verify error safety** (test_policy_objects.py:89-108)
   ```python
   def test_from_rate_unknown_period(self) -> None:
       with pytest.raises(ThrottleDeclarationError, ...) as exc_info:
           RateLimit.from_rate("10/fortnight")
       assert exc_info.value.context.get("rate") == "10/fortnight"
       assert exc_info.value.context.get("period") == "fortnight"
   ```
   - Context is checked for rate string and period string; no sensitive data leakage.

---

## Immutability and Function Integrity

**Requirement:** Policy is attached as an immutable object; function is not modified (no side effects to signature, execution, or attributes except the policy attachment).

### Finding: PASS

**Evidence:**

1. **ThrottlePolicy is frozen** (policy_objects.py:87-88)
   ```python
   @dataclass(frozen=True, slots=True)
   class ThrottlePolicy: ...
   ```
   - Once attached, the policy cannot be modified.

2. **Function unmodified except for single attribute** (throttled_client.py:34-37)
   ```python
   def declare(func: Decorated) -> Decorated:
       setattr(func, const.THROTTLE_POLICY_ATTR, policy)
       return func
   ```
   - Only `setattr()` call; all other attributes left intact.
   - Function object, signature, bytecode untouched.

3. **Test confirms no side effects** (test_throttled_client.py:33-54)
   ```python
   def test_decorator_preserves_function_identity_with_args(self) -> None:
       def add(a: int, b: int) -> int:
           return a + b

       original_id = id(add)
       decorated = throttled(scope="math.add", rate="1000/second")(add)

       assert id(decorated) == original_id
       assert decorated is add
       assert decorated(2, 3) == 5
   ```
   - Identity preserved, execution unchanged.

---

## Dependency Surface: Policy Objects + Constants

**Requirement:** No homegrown throttling, no framework-specific imports. Only imports are policy objects and constants.

### Finding: PASS

**Evidence:**

1. **Imports in throttled_client.py**
   ```python
   from collections.abc import Callable, Mapping
   from typing import Any, TypeVar

   from monitoring_suite.api_limiter.services.constants import policy as const
   from monitoring_suite.api_limiter.services.policy.policy_objects import (
       RateLimit,
       ThrottlePolicy,
       TierRate,
   )
   ```
   - `collections.abc`, `typing`: stdlib only.
   - `constants`, `policy_objects`: internal, dependency-light modules.
   - No external HTTP, caching, storage, or framework libraries.

2. **No decorator framework dependencies:** Does not import from `functools`, `wrapt`, or other decorator utilities (which would suggest wrapping logic).

3. **Minimal module footprint:** throttled_client.py is 52 lines total; Throttled class is 49 lines. Simple, obvious flow; no hidden complexity.

---

## Verdict

**Status: PASS**

All security properties satisfied:
- Declaration integrity: all validation fires at decoration time via policy object constructors.
- Non-enforcement posture: decorator is pure metadata; no wrapping, counting, or execution interception.
- Attribute hygiene: uses `__throttle_policy__` constant exclusively; PolicyRegistry type-guards.
- Error metadata: safe (scope, rate, tier labels, counts); no secrets or personal data.
- Immutability: policy is frozen; function unmodified except for metadata attachment.
- Dependency surface: stdlib + policy objects only; no external or framework-specific dependencies.

No findings. Decorator is a safe, transparent metadata appliance.
