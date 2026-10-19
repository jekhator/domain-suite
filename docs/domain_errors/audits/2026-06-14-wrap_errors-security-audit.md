# @wrap_errors Decorator Security Audit

**Date:** 2026-06-14  
**Feature:** `wrap_errors` decorator, `WrapErrorsClient` class, argument capture, exception wrapping  
**Scope:** `domain_errors/decorators/wrap_errors/wrap_errors_client.py` + tests + documentation

## Findings

### Code Execution / Injection

**Status: No defects.**

The decorator performs no `eval`, `exec`, `compile`, or deserialization of untrusted input. Argument capture uses `inspect.signature(func).bind(*args, **kwargs).apply_defaults()`, which is a pure, safe reflection API:it reads parameter names and applies default values without executing code.

Verification: Test with dangerous arg names (`__dict__`, `exec`) and string values that look like formulas (`"1+1"`) confirms they are captured as literals, not executed.

```python
@wrap_errors(TestError)
def danger(x: int, __dict__: int, exec: int) -> None:
    raise ValueError("fail")

try:
    danger(1, 2, 3)
except TestError as e:
    assert e.context == {'x': 1, '__dict__': 2, 'exec': 3}  # No code execution
```

### Denial of Service

**Status: No defects.**

The decorator performs bounded operations:
- `inspect.signature()` call: O(1) cost per decorated function (computed at decoration time, not per call).
- `signature.bind()`: O(n) in parameter count (typically <50 parameters), occurs once per exception.
- No recursion, no unbounded loops, no memory allocation proportional to exception depth.

Signature binding failure (e.g., mismatched args) raises `TypeError` (a native Python error), which is not caught by the decorator's exception handler unless explicitly in the `catch` tuple; it propagates raw.

### Data Exposure / Logging (PRIMARY FINDING)

**Status: Data-handling guidance required : risk PRESENT with default settings.**

**The Issue:**  
With `capture=True` (the DEFAULT), **ALL function arguments flow into `DomainError.context`**, which is designed to emit into structured logs. A function taking secrets (password, API key, token, PII, authentication credentials) will leak them into error context and log outputs.

**Example:**
```python
@wrap_errors(AuthError)  # capture=True by default
def authenticate(username: str, password: str) -> str:
    if not password:
        raise ValueError("Missing password")
    return f"auth_token_for_{username}"

try:
    authenticate("alice", "secret_password_123")
except AuthError as err:
    # err.context == {'username': 'alice', 'password': 'secret_password_123'}
    # This dict flows into logging -> exposing the plaintext secret.
    logger.error("Auth failed", extra=err.to_log_extra())
```

**Severity: MEDIUM.**  
The risk is real but **mitigatable and explicitly documented**. The library provides clear opt-out via `capture=False`, and Example 5 of the public documentation shows exactly this use case. However:

1. **Default captures by default:** New users may not realize arguments are captured; the default-True setting makes secrets leakage easy if not carefully read.
2. **Context is opaque:** There is no field-level masking or per-argument sensitivity tagging; all arguments are captured as-is.
3. **No redaction on emission:** The library does not redact before emitting to logs. Redaction responsibility falls to the caller's logging pipeline.

**Documented Mitigations (Already Present):**
- Parameter `capture=False` explicitly disables all argument capture.
- Example 5 in `docs/apps/wrap_errors.md` demonstrates this pattern for authentication functions.
- Parameter description states: "Set `False` to omit arguments (e.g., for functions handling secrets)."

**Verification (test runs):**
```
PASS: test_capture_false_empty_context: capture=False yields {} context
PASS: test_capture_false_sync_with_defaults_still_empty: defaults NOT included when capture=False
```

### Never-Swallow Behavior

**Status: No defects.**

The decorator always re-raises caught exceptions:
- Lines 51, 62 (sync + async): `raise self._as_domain(error, func, args, kwargs) from error`
- No silent suppression, no exception-swallowing code paths.
- DomainError instances are re-raised unchanged (lines 48-49, async; 59-60, sync) without catching them.

Test coverage confirms: 45 tests, all passing, including explicit pass-through tests for `DomainError` (no `__cause__` added when DomainError is raised natively).

### BaseException Safety

**Status: No defects.**

The `catch` parameter is typed as `tuple[type[Exception], ...]` (line 23, wrap_errors_client.py). Python's exception-handling syntax (`except self.catch`) respects this tuple and does not catch `BaseException` subclasses outside of `Exception` (e.g., `KeyboardInterrupt`, `SystemExit`, `GeneratorExit`).

Verification (negative control):
```
PASS: KeyboardInterrupt + catch=(Exception,) -> propagates raw (not wrapped)
PASS: SystemExit + catch=(Exception,) -> propagates raw (not wrapped)
```

### Traceback Preservation

**Status: No defects.**

The `raise ... from error` syntax (lines 51, 62) explicitly chains the original exception as `__cause__`, preserving the exception's `__traceback__`. Python's traceback machinery automatically includes the full chain.

Verification:
```
PASS: Wrapped DomainError.__cause__ is the original exception (ZeroDivisionError)
PASS: Original traceback preserved: e.__cause__.__traceback__ is not None
```

### DomainError Pass-Through

**Status: No defects.**

Lines 48-49 (async) and 59-60 (sync):
```python
except DomainError:
    raise
```

If the decorated function raises a `DomainError` (or subclass), it is re-raised immediately, unchanged. No double-wrapping, no `__cause__` added, no context injection. Tests verify this behavior (TestWrapErrorsDomainErrorPassthrough).

### I/O, Subprocess, Filesystem, Network

**Status: No exposed surface.**

The decorator is stateless, in-memory only. No I/O, file access, network calls, or subprocess invocation.

### Secrets Handling / Key Material

**Status: Partially applicable (via argument capture).**

This decorator does not manage, store, or transmit secrets itself. However, **it captures function arguments including secrets** and passes them to `ErrorChain.wrap()` as context. See "Data Exposure / Logging" above.

### Authentication / Authorization

**Status: Not applicable.**

No authentication, authorization, or privilege boundary enforcement.

### Multi-Tenant Data Isolation

**Status: Not applicable.**

The library is single-tenant in design; data isolation is the responsibility of calling code.

### Async Safety

**Status: No defects.**

The decorator correctly detects async functions via `inspect.iscoroutinefunction()` and builds an async wrapper that awaits the coroutine before catching exceptions. Behavior is identical to the sync path. Tests cover both sync and async paths (45 tests total, with dedicated async test classes).

### functools.wraps Preservation

**Status: No defects.**

Both sync and async wrappers use `@functools.wraps(func)` (lines 44, 55), preserving the original function's `__name__`, `__doc__`, `__module__`, `__qualname__`, and `__annotations__`. Tests verify this (TestWrapErrorsFunctoolsWraps).

## Conclusion

**Verdict: PASS-WITH-RECOMMENDATIONS**

No code-level security defects. The @wrap_errors decorator is well-designed with no code-execution, denial-of-service, traceback, or pass-through vulnerabilities.

**Primary note:** Sensitive-data capture via the default `capture=True` is **documented and mitigatable** but warrants emphasis in consumer guidance. The risk is standard for exception-context-capturing libraries; the library provides the escape hatch (`capture=False`) and Example 5 documents the secret-handling pattern.

### Recommendations (Non-Critical, Future Enhancements)

1. **Strengthen sensitivity guidance in wrap_errors.md:**
   - Add a **"Sensitive Data Handling"** section (parallel to Example 5) that explicitly warns: "If your decorated function handles passwords, API keys, authentication tokens, or PII, set `capture=False` to prevent argument leakage into logs."
   - Link to sensitivity-mixin (upcoming suite package) for future field-level redaction patterns.

2. **Future integration with sensitivity-mixin:**
   - Once sensitivity-mixin ships with field-level masking (V1 scope), consider a follow-on enhancement: a `redact_fields: tuple[str, ...] | None = None` parameter on the decorator to selectively mask sensitive argument names before emission.
   - This would be a V0.2+ enhancement, not required for v0.1.0.

3. **Callable-level documentation:**
   - Consider adding a docstring note to `WrapErrorsClient.__init__` or `wrap_errors()` factory: "Decorates sync and async callables; captures arguments into context by default:set capture=False for functions handling secrets."

## Verification Contract Fulfilled

- PASS: **catch type confirmed:** `catch: tuple[type[Exception], ...]` (not BaseException)
- PASS: **capture=False test passing:** `test_capture_false_empty_context` confirms empty dict when disabled
- PASS: **Full test suite passing:** 45 tests, all green
- PASS: **BaseException safety:** KeyboardInterrupt and SystemExit propagate raw (negative control passed)
- PASS: **Never-swallow confirmed:** All exception paths re-raise with `raise ... from error`
- PASS: **Code-execution test:** Dangerous arg names and formula strings captured as literals, no eval/exec
- PASS: **Traceback preservation:** Original exception's `__traceback__` preserved via `__cause__`
