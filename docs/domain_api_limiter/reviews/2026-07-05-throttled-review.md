# Throttled Decorator Feature Review

**Date:** 2026-07-05  
**Branch:** feat/v01-policy  
**Verdict:** CHANGES-REQUIRED

## Scope

| File | Lines | Role |
|------|-------|------|
| `domain_api_limiter/decorators/throttled/throttled_client.py` | 52 | Throttled decorator factory and module handle |
| `domain_api_limiter/decorators/throttled/__init__.py` | 8 | Public re-exports |
| `domain_api_limiter/decorators/tests/test_throttled/test_throttled_client.py` | 487 | Tests for decorator |

## Standards Dimensions Checked (derived from source-of-truth)

1. **Frozen dataclass with slots=True** - N/A; Throttled is a decorator factory, not a DTO.
2. **Facade ban (no module-level domain functions)** - Throttled class encodes declaration logic in __call__ method; the module-level `throttled = Throttled()` instance (line 51) is a sanctioned handle pattern (analogous to domain-security's `requires`).
3. **objects/client split** - N/A; single client class with no separate objects module.
4. **Absolute imports** - All imports use absolute paths; no relative imports.
5. **__all__ + combined re-export idiom** - throttled/__init__.py combines imports (Throttled, throttled) in single statement, __all__ sorted alphabetically.
6. **One-line docstrings on every method, factory, property, validator** - Throttled class (line 19): "Decorator factory attaching a validated ThrottlePolicy to a callable." __call__ method (line 27): "Return a declaration decorator for the scope, rate, and tier overrides." _tier_rates static method (line 41): "Build tier overrides from a tier-to-rate mapping." BLOCKING FINDING: Inner declare function (line 34) lacks docstring (see Findings).
7. **No inline # comments** - No inline comments found.
8. **Intuitive variable names, no single-letter TypeVars** - Decorated TypeVar (line 15) is descriptive: `Decorated = TypeVar("Decorated", bound=Callable[..., Any])`. Good.
9. **Signature stacking (3+ params after self/cls)** - __call__ (line 21-26) has 3 params after self (scope, rate, tiers); params are correctly stacked on separate lines. PASS.
10. **Constants module** - N/A; constants imported from domain_api_limiter.services.constants.policy.
11. **Error messages via const.ERR_*** - Errors from policy.py constants; not defined in this module.
12. **Test<Concern> classes + fixtures-in-conftest + per-feature concern dirs** - test_throttled_client.py has TestThrottledDecoratorIdentityContract, TestThrottledDecoratorPolicyAttachment, TestThrottledDecoratorWithTiers, TestThrottledDecoratorValidation, TestThrottledModuleHandle, TestThrottledMultipleDecorations, TestThrottledComplexScenarios. All follow Test<Concern> pattern. No conftest fixtures needed (none used).
13. **100% coverage** - Coverage report: throttled_client.py 100% (19 stmts, 0 miss).
14. **collections.abc over typing ABCs** - Line 5: `from collections.abc import Callable, Mapping` correctly imported from collections.abc, not typing.
15. **No RST/Sphinx markup** - All docstrings plain prose.
16. **DTO field-grouping** - N/A; decorator, not a DTO.
17. **Module docstrings** - throttled_client.py (line 1): "Declarative rate-limit policy attachment for service callables." (one-line, on-point). Good.
18. **Multi-value constant collections use frozenset** - N/A.
19. **TypeVar/ParamSpec naming** - Decorated is descriptive. PASS.

## Findings

### Blocking

1. **Missing docstring on inner function** (BLOCKING/NIT border, trivial fix)  
   **File:** `domain_api_limiter/decorators/throttled/throttled_client.py:34`  
   **Issue:** Inner `declare` function has no docstring.  
   **Current:**
   ```python
   def declare(func: Decorated) -> Decorated:
       setattr(func, const.THROTTLE_POLICY_ATTR, policy)
       return func
   ```
   **Expected:** One-line docstring per standards (every method/factory has one). Suggest: `"""Attach policy to the function and return it unchanged."""`

### Warning

None beyond the blocking item.

## OBA Compliance Attestation

This review attests that domain-api-limiter (throttled decorator feature) conforms to published standards for Python package development: decorator-factory pattern (no facade violations), test structure, docstring discipline, and imports. The codebase undergoes no scanning for internal brand/employer identifiers; review focuses on structure and standards conformity only. Code is generic and portable across deployment contexts.

## Verdict

**CHANGES-REQUIRED**

One blocking finding: missing docstring on the `declare` inner function. Trivial fix; all other standards dimensions pass. Fix docstring and re-run review.

---

**Review reconciliation (2026-07-05): verdict SHIP.** The flagged inner `declare` closure docstring is NOT applied: the freshest merged exemplars (domain-security `requires_client.py` / `tenant_scoped_client.py` and domain-errors `wrap_errors_client.py`) leave inner decorator-factory closures (`decorate`, `wrapper`, `async_wrapper`) docstring-free; the one-line-docstring standard governs module/class/method surfaces, not nested closures. Adding it here would diverge from the exemplar. The underlying question (should inner closures carry docstrings suite-wide) is logged to the refactor round for a single ruling applied to every package at once.
