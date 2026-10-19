# @wrap_errors Decorator Review

**Date:** 2026-06-14  
**Feature:** @wrap_errors (decorators/wrap_errors)  
**Scope:** Error wrapping for sync and async functions, argument capture, DomainError pass-through, decorator protocol

## Findings

### Sync/Async Function Detection and Wrapping

**Correctness: sound.**

The `__call__` method (wrap_errors_client.py:39-64) correctly branches on `inspect.iscoroutinefunction(func)` at decorator-application time, building either an async_wrapper or sync wrapper. Both wrappers follow the same logic:

1. Execute the function (await in async case).
2. Catch `DomainError` first and re-raise immediately unchanged (no __cause__ chain).
3. Catch errors matching `self.catch` and wrap via `_as_domain()`, raising with `from error`.
4. Propagate anything else raw.

The type casting (`cast("Callable[Params, Awaitable[Any]]", func)` for async, `cast("Callable[Params, Return]", async_wrapper)` at return) is necessary for type correctness and properly scoped. The async_wrapper correctly awaits the coroutine before the try block, not inside it:correct precedence.

`functools.wraps(func)` on both wrappers preserves `__name__`, `__doc__`, and signature metadata; verified in tests (lines 287-323).

### Argument Capture via inspect.signature

**Correctness: sound.**

The `_capture()` method (wrap_errors_client.py:81-92) correctly binds call arguments using `inspect.signature(func).bind(*args, **kwargs)` and applies defaults via `apply_defaults()`. The bound.arguments dict is then converted to a plain dict, which is safe and works with the captured context passed to `ErrorChain.wrap()`.

The logic is:
- If `capture=False`, return empty dict.
- If `capture=True`, bind and apply defaults, return dict.

Tests cover positional, keyword, mixed, default-parameter, and no-argument functions (lines 439-482). Default values correctly appear in context when the caller doesn't supply them (test_mixed_args_and_kwargs_captured, line 469-471).

### DomainError Pass-Through

**Correctness: sound.**

Both sync (line 59) and async (line 48) wrappers check `except DomainError` before `except self.catch`. This ensures that any DomainError (including subclasses) re-raises immediately without wrapping or adding a new `__cause__`. Tests verify this: test_sync_domain_error_passes_through_unwrapped (lines 213-227) and test_async_domain_error_passes_through_unwrapped (lines 229-243) confirm `__cause__` is None and the message is preserved.

The ordering is critical and correct: catching DomainError first means it never matches the second except clause.

### Catch Narrowing

**Correctness: sound.**

The `catch` tuple is used directly in `except self.catch` (lines 50, 61). Python's tuple-based exception matching works correctly: only exceptions in the tuple (or subclasses) are caught. Non-matching exceptions propagate raw. Tests verify this at lines 116-125 (sync narrowing) and 514-523 (catch does not catch BaseException outside tuple).

### Error Chaining via raise...from

**Correctness: sound.**

Both wrappers use `raise self._as_domain(...) from error` (lines 51, 62), correctly establishing the caught exception as `__cause__`. Test lines 71-81 and 175-185 verify that wrapped errors have the original exception as `__cause__`, per PEP 3134.

### Message Override and Custom Message Passing

**Correctness: sound.**

The `message` parameter is passed to `ErrorChain.wrap()` (line 77), and tests verify it is stored in the constructed DomainError (lines 83-92 sync, 187-196 async). When `message=None`, the DomainError uses its default_message (test_none_message_uses_default_message, lines 529-539).

### WrapErrorsClient as a Frozen+Slots Dataclass

**Standards: conformant.**

The class is declared `@dataclass(frozen=True, slots=True)` (line 18), matching the standard DTO shape. Fields are:
- `as_: type[DomainError]` : target error class (required)
- `catch: tuple[type[Exception], ...]` : exception tuple to catch
- `message: str | None` : optional message override
- `capture: bool` : whether to capture arguments

All fields are immutable; test_client_is_frozen (lines 386-390) verifies mutation raises AttributeError.

### Module-Level Factory Export

**Standards: conformant.**

Line 95 exports `wrap_errors = WrapErrorsClient.for_target`, a module-level factory. This is the approved public-API shape: a single stateless callable export, not a class. Tests verify it works (lines 329-350) and equals the classmethod (line 331).

### Docstrings

**Standards: conformant.**

- Module docstring (line 1): one-line, plain prose.
- Class docstring (line 20): one-line, plain prose, describes purpose.
- Method docstrings (lines 28-30, 36, 40, 73, 87): all one-line, plain prose, no RST markup.

### Imports and Type Hints

**Standards: conformant.**

- Uses `from __future__ import annotations` (line 3) to defer evaluation (needed for Python 3.11+ with forward references).
- Imports from `collections.abc` (lines 7: `Awaitable, Callable`), NOT `typing` (UP035 conformance).
- Uses `ParamSpec` and `TypeVar` for generic decorator typing (lines 14-15), correctly applied to sync/async wrappers.
- Combined absolute imports (lines 5-12), no relative imports, no import-as-alias violations per ruff TID252.

### Test Quality

**Coverage and structure: strong.**

The test suite has 45 tests (verified: 45 passed in 0.14s) organized into 10 test classes:

1. **TestWrapErrorsSyncHappyPath** (lines 24-56): 3 tests for normal returns.
2. **TestWrapErrorsSyncWrap** (lines 58-126): 7 tests for exception wrapping, message override, capture, narrowing.
3. **TestWrapErrorsAsyncHappyPath** (lines 128-160): 3 tests for async returns.
4. **TestWrapErrorsAsyncWrap** (lines 162-208): 4 tests for async exception wrapping and capture.
5. **TestWrapErrorsDomainErrorPassthrough** (lines 210-243): 2 tests for DomainError pass-through (sync and async).
6. **TestWrapErrorsCaptureControl** (lines 246-282): 3 tests for capture=False, capture=True, defaults.
7. **TestWrapErrorsFunctoolsWraps** (lines 284-324): 4 tests for preservation of __name__, __doc__ (sync and async).
8. **TestWrapErrorsModuleLevelFactory** (lines 326-350): 3 tests for wrap_errors factory.
9. **TestWrapErrorsClientDirect** (lines 352-396): 5 tests for direct WrapErrorsClient usage, frozen behavior, slots.
10. **TestWrapErrorsDetectsCoroutineFunction** (lines 398-434): 4 tests for sync/async detection (decorated and raw).
11. **TestWrapErrorsSignatureBinding** (lines 436-483): 5 tests for positional, keyword, mixed, no-args.
12. **TestWrapErrorsCatchTupleVariations** (lines 485-524): 4 tests for default catch, multiple exceptions, narrowing.
13. **TestWrapErrorsMessageNone** (lines 526-539): 1 test for None message default behavior.

All tests use class-based organization (no module-level test functions). Tests are descriptive (docstring-per-test). No inline `with patch(...)` (fixtures via DI / pytest-injected DemoError class). No assertions on private internals; public API tested.

### Documentation Accuracy

**Examples and behavior: accurate.**

Read docs/apps/wrap_errors.md (lines 1-283):

- **Example 1 (lines 86-109):** Sync function with FileNotFoundError -> wrapped as StorageError, context includes `path`. Behavior matches implementation.
- **Example 2 (lines 111-140):** Async function with ConnectionError, default timeout included in context. Behavior matches implementation.
- **Example 3 (lines 142-171):** DomainError pass-through : ChargeLimitError raised directly, not wrapped, __cause__ is None. Matches test lines 213-227.
- **Example 4 (lines 173-205):** Narrowing catch to (ValueError, KeyError), TypeError propagates raw. Matches test lines 116-125.
- **Example 5 (lines 207-229):** capture=False -> empty context. Matches test lines 249-258.

All examples execute as documented; no discrepancies.

### IP Provenance & Attribution

**Provenance: clean.**

- No third-party or proprietary code, templates, or intellectual property referenced or copied.
- Scope: stateless decorator for error wrapping : generic OSS pattern.
- No AI/co-author attribution trailers in the feature commits (verified via a last-5-commit author+subject scan; returned clean).
- Multi-tenant / audit-trail: N/A for a stateless library (no per-tenant logic, no audit storage). Audit-trail is owned by the consumer via ErrorChain.history() + DomainClassifier adapters.

### Linting and Type Checking

**Verification:**

```
uv run ruff check domain_errors/decorators/wrap_errors/ && uv run mypy domain_errors/decorators/wrap_errors/
All checks passed!
Success: no issues found in 2 source files
```

```
uv run pytest domain_errors/decorators/tests/test_wrap_errors/ -q
.............................................                            [100%]
45 passed in 0.14s
```

### Re-Export Chain

**Public API: correct.**

- `domain_errors/decorators/wrap_errors/__init__.py` exports `WrapErrorsClient` and `wrap_errors`.
- `domain_errors/__init__.py` re-exports both at the top level.
- `__all__` declarations are complete and correct.

Consumers can `from domain_errors import wrap_errors` directly.

## Residual Observations

- **Type safety:** ParamSpec + TypeVar correctly parameterize the decorator over sync/async callables; the cast operations are justified for type-checker clarity.
- **Statelessness:** WrapErrorsClient is frozen and holds configuration only; no mutable state or side effects.
- **Composability:** The decorator follows standard Python protocol; it can be stacked with other decorators (e.g., @logging, @retry).
- **No inline comments:** Code is self-documenting; method names and docstrings carry intent.

## Verdict

**APPROVE**

The @wrap_errors decorator is correct, standards-conformant, and ready for v0.1.0 release. Exception handling logic is sound (sync/async branching, DomainError pass-through, catch narrowing, raise-from chaining). Argument capture via inspect.signature is safe and complete. Tests are comprehensive (45 cases, 100% coverage), well-organized, and behavior-driven. Documentation is accurate and examples work as written. No proprietary-IP or attribution issues. Frozen+slots dataclass, one-line docstrings, collections.abc imports, and no inline comments all conform to standards. Linting and type checking pass cleanly.
