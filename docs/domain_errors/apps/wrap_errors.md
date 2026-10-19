# domain-errors. @wrap_errors Decorator

> **Location:** `domain_errors/decorators/wrap_errors/wrap_errors_client.py`
> **Status:** Implemented and fully tested in v0.1.0+.
> **Code location:** `domain_errors/decorators/wrap_errors/wrap_errors_client.py`
> **Sibling docs:** `docs/apps/domain_error.md`, `docs/apps/chain.md`, `docs/apps/diagrams.md`

## Purpose

`wrap_errors` is a function decorator that automatically wraps caught exceptions into a target `DomainError` via `ErrorChain.wrap()`, enabling declarative error handling without boilerplate try-except-raise-from blocks. Use it to convert foreign (non-DomainError) exceptions into domain-specific errors, capture function arguments into error context for structured logging, and let `DomainError` instances pass through unchanged.

It is the suite-wide error-wrapping **standard** for all OSS packages: the decorator analog of manual `ErrorChain.wrap(...) + raise ... from e`.

## Core Design

The decorator is **configurable** and works on both **sync and async callables**. It satisfies the standard Python decorator protocol:

```python
@wrap_errors(MyDomainError, catch=(ValueError, KeyError), message="...", capture=True)
def my_func(x: int, y: str) -> Result:
    ...
```

The decorator:
- Runs the decorated function
- Catches exceptions matching the `catch` tuple
- Calls `ErrorChain.wrap(error, as_=..., message=..., **captured_args)` to construct a domain error
- Raises the domain error with `raise ... from error` (so `__cause__` is the original exception)
- **Passes `DomainError` (and subclasses) through unchanged**: never re-wraps
- Captures the call's bound arguments (with defaults applied) into the domain error's `.context`, unless disabled with `capture=False`
- Works transparently on async functions (awaits the coroutine)
- Preserves the original function's `__name__`, `__doc__`, and signature via `functools.wraps`

## The WrapErrorsClient Class and wrap_errors Factory

### Instance / Factory

```python
from domain_errors import wrap_errors

@wrap_errors(MyError, catch=(ValueError,))
def process_data(x: int) -> str:
    ...
```

The public API is **`wrap_errors`**, which is `WrapErrorsClient.for_target()`, a classmethod factory. You do not instantiate `WrapErrorsClient` directly.

### Signature

```python
wrap_errors(
    as_: type[DomainError],
    *,
    catch: tuple[type[Exception], ...] = (Exception,),
    message: str | None = None,
    capture: bool = True,
) -> WrapErrorsClient
```

The returned `WrapErrorsClient` instance is callable; when applied to a function, it returns a wrapped version.

## Parameters

- **`as_`**: the target `DomainError` subclass to wrap into (required, positional). Exceptions matching `catch` will be wrapped into this type via `ErrorChain.wrap()`.
- **`catch`**: tuple of `Exception` types to catch (default `(Exception,)`). Only exceptions in this tuple (or subclasses) are wrapped; others propagate raw. Typed as `tuple[type[Exception], ...]`. Note: `BaseException` (e.g., `KeyboardInterrupt`, `SystemExit`) is intentionally NOT catchable.
- **`message`**: optional override message passed to the constructed `DomainError` (default `None`). If provided, used instead of `DomainError.default_message`.
- **`capture`**: when `True` (default), the decorated call's bound arguments are captured into the `DomainError`'s `.context` dict via `inspect.signature(func).bind(...) + apply_defaults()`. Set `False` to omit arguments (e.g., for functions handling secrets).

## Behavior

On each call to a decorated function:

1. **Execute the function.** If it returns normally, the return value flows through unchanged.
2. **Catch exceptions.** If an exception is raised:
   - If it is a `DomainError` (or subclass), **re-raise it immediately, unchanged.** No wrapping, no new `__cause__`.
   - If it matches an exception type in `catch`, **wrap it**: call `ErrorChain.wrap(error, as_=..., message=..., **captured_args)`, then `raise <domain_error> from error` (chaining via `__cause__`).
   - Otherwise, **propagate raw.** The exception is not caught by the decorator.
3. **Argument capture.** When `capture=True`, `inspect.signature(func).bind(*args, **kwargs).apply_defaults()` extracts all bound parameters (including defaults) as a `dict[str, Any]`, which is passed to `ErrorChain.wrap()` as context kwargs. When `capture=False`, an empty dict is passed (no context). If the call's arguments do not match the function signature, binding fails; the wrapper then passes an empty context and still raises the `DomainError` from the original `TypeError`.

### Async Support

The decorator detects `inspect.iscoroutinefunction(func)` and builds an async wrapper that awaits the coroutine before catching. Behavior is identical to the sync path.

## Sensitive Data Handling

`capture=True` (the default) records the decorated function's bound arguments in the raised `DomainError`'s `.context`, which is designed to flow into structured logs. **If a decorated function receives secrets or PII** (passwords, tokens, API keys, personal data), those values are captured into the error context and can reach your logs.

For any function handling sensitive inputs, set **`capture=False`** to omit all arguments from the error context (see Example 5):

```python
@wrap_errors(AuthError, catch=(ValueError,), capture=False)
def authenticate(username: str, password: str) -> str:
    ...
```

Guidance:
- Default to `capture=False` on authentication, payment, and PII-handling functions.
- Argument capture is all-or-nothing in v0.1.0; field-level redaction (e.g. via a sensitivity-mixin integration) is a planned future enhancement.
- Captured context is emitted verbatim: redaction is the consumer's logging-pipeline responsibility until field-level support ships.

## Examples

### Example 1: Sync wrap with captured context

```python
from domain_errors import DomainError, wrap_errors, ErrorChain

class StorageError(DomainError):
    code = "storage_error"
    domain = "storage"
    http_status = 503

@wrap_errors(StorageError, catch=(FileNotFoundError, IOError), message="File operation failed")
def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()

try:
    read_file("/nonexistent/file.txt")
except StorageError as err:
    print(f"Error: {err.message}")
    print(f"Context: {err.context}")
    # Output:
    # Error: File operation failed
    # Context: {'path': '/nonexistent/file.txt'}
```

### Example 2: Async wrap

```python
import asyncio
from domain_errors import DomainError, wrap_errors

class ApiError(DomainError):
    code = "api_error"
    domain = "api"
    http_status = 502

@wrap_errors(ApiError, catch=(ConnectionError, TimeoutError))
async def fetch_data(url: str, timeout: int = 30) -> dict:
    # Simulated async call
    if url == "":
        raise ConnectionError("Invalid URL")
    return {"data": "result"}

async def main():
    try:
        await fetch_data("")
    except ApiError as err:
        print(f"Error: {err.message}")
        print(f"Context: {err.context}")
        # Output:
        # Error: An unspecified domain error occurred.  (no message=, so default_message)
        # Context: {'url': '', 'timeout': 30}

asyncio.run(main())
```

### Example 3: DomainError pass-through

```python
from domain_errors import DomainError, wrap_errors

class PaymentError(DomainError):
    code = "payment_error"
    domain = "payment"
    http_status = 402

class ChargeLimitError(PaymentError):
    code = "charge_limit_exceeded"

@wrap_errors(PaymentError, catch=(ValueError, KeyError))
def charge_card(amount: int) -> str:
    if amount > 10000:
        # Raise a DomainError directly; the decorator passes it through
        raise ChargeLimitError(message="Amount exceeds limit", amount=amount)
    return f"Charged ${amount/100:.2f}"

try:
    charge_card(50000)
except PaymentError as err:
    print(f"Code: {err.code}")
    print(f"Message: {err.message}")
    # Output:
    # Code: charge_limit_exceeded
    # Message: Amount exceeds limit
    # Note: err.__cause__ is None (not re-wrapped)
```

### Example 4: Narrowing catch to specific errors

```python
from domain_errors import DomainError, wrap_errors

class DataError(DomainError):
    code = "data_error"
    domain = "data"
    http_status = 400

@wrap_errors(DataError, catch=(ValueError, KeyError))
def parse_record(data: dict, key: str) -> int:
    # Only ValueError and KeyError are caught and wrapped.
    # A TypeError, for example, propagates raw.
    value = data[key]  # KeyError -> wrapped as DataError
    return int(value)  # ValueError if value is not numeric -> wrapped as DataError

try:
    parse_record({}, "missing_key")
except DataError as err:
    print(f"Wrapped: {err.code}")

try:
    parse_record({"key": "not_a_number"}, "key")
except DataError as err:
    print(f"Wrapped: {err.code}")

try:
    # A TypeError is NOT in catch, so it propagates raw (unexpected errors stay visible)
    parse_record(None, "key")  # None["key"] raises TypeError
except TypeError as err:
    print(f"Raw TypeError: {err}")
```

### Example 5: Disabling argument capture for secrets

```python
from domain_errors import DomainError, wrap_errors

class AuthError(DomainError):
    code = "auth_error"
    domain = "auth"
    http_status = 401

@wrap_errors(AuthError, catch=(ValueError,), capture=False)
def authenticate(username: str, password: str) -> str:
    if not password:
        raise ValueError("Password required")
    return f"Token for {username}"

try:
    authenticate("alice", "")
except AuthError as err:
    print(f"Context: {err.context}")
    # Output:
    # Context: {}  (no args captured)
```

### Example 6: Class-level decoration (fans out to all public methods)

```python
from domain_errors import DomainError, wrap_errors
import asyncio

class PaymentError(DomainError):
    code = "payment_error"
    domain = "payment"
    http_status = 402

@wrap_errors(PaymentError, catch=(ValueError, IOError))
class PaymentService:
    def __init__(self, rate_limit: int = 100) -> None:
        self.rate_limit = rate_limit

    def validate_amount(self, amount: int) -> bool:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.rate_limit:
            raise ValueError("Amount exceeds rate limit")
        return True

    async def charge_card(self, card_token: str, amount: int) -> str:
        if not card_token:
            raise ValueError("Card token required")
        return f"Charged {amount} on {card_token}"

service = PaymentService(rate_limit=5000)

assert service.validate_amount(100)

with pytest.raises(PaymentError) as exc_info:
    service.validate_amount(-50)
assert exc_info.value.__cause__.__class__ == ValueError
assert exc_info.value.context == {"amount": -50}

result = asyncio.run(service.charge_card("tok_visa", 1000))
assert "Charged 1000" in result

with pytest.raises(PaymentError):
    asyncio.run(service.charge_card("", 1000))
```

**Class-level behavior:**
- Decorating a class fans out the decorator over all public callables in `cls.__dict__`.
- Sync methods get the sync wrapper; async methods get the async wrapper (handling preserved per method).
- Private methods (prefixed with `_`), dunder methods (e.g., `__init__`), properties, and nested classes are skipped.
- Classmethod and staticmethod are unwrapped, decorated, and rewrapped to preserve their semantics.
- Methods already decorated with `@wrap_errors` (marked with `__wrap_errors_applied__`) are left untouched (override detection).
- The `capture`, `message`, and `catch` parameters apply uniformly to all fanned methods.
- Arguments `self` and `cls` are automatically filtered from the error context to avoid object serialization issues.

## Usage with ErrorChain

After the decorator wraps an error, walk the chain to classify foreign exceptions and log structured data:

```python
from domain_errors import DomainError, ErrorChain, wrap_errors
from domain_errors.domains.python import python

class ServiceError(DomainError):
    code = "service_error"
    domain = "service"
    http_status = 500

@wrap_errors(ServiceError, catch=(FileNotFoundError, OSError), message="Service failed")
def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return {"config": f.read()}

try:
    load_config("/etc/missing.yaml")
except ServiceError as err:
    # Walk the chain and classify exceptions
    links = ErrorChain.history(err, classifiers=(python,))
    for link in links:
        print(f"{link.type_name} ({link.domain}): {link.message}")
        # Output:
        # FileNotFoundError (python): [Errno 2] No such file or directory: '/etc/missing.yaml'
        # ServiceError (service): Service failed
    
    # Get crossings (domain boundary hops)
    crossings = ErrorChain.crossings(err, classifiers=(python,))
    for crossing in crossings:
        print(f"{crossing.cause.domain} -> {crossing.effect.domain}")
        # Output:
        # python -> service
```

## Design Notes

- **Decorator pattern:** Standard Python decorator returning a wrapped callable; composes with other decorators.
- **DomainError pass-through:** If the function itself raises a `DomainError`, the decorator re-raises it unchanged. This prevents double-wrapping and respects the semantic intent of the original domain error.
- **Argument capture via `inspect.signature()`:** Safe for positional, keyword, and default arguments. Defaults are applied automatically, so context includes full parameter state.
- **Narrowing `catch`:** Encourage consumers to narrow `catch` to known error families (e.g., `catch=(FileNotFoundError, IOError)` rather than `catch=(Exception,)`). This preserves unexpected errors as signals for bugs.
- **Async detection:** Uses `inspect.iscoroutinefunction()` to detect coroutines; the async wrapper awaits before catching.
- **functools.wraps:** Preserves `__name__`, `__doc__`, and signature metadata on the returned function.
- **Stateless:** `WrapErrorsClient` is a frozen dataclass with no mutable state. Safe to share across calls and threads.

## See Also

- **ErrorChain:** `docs/apps/chain.md`: how to walk chains and use classifiers
- **DomainError Base:** `docs/apps/domain_error.md`: how to define domain-specific errors
- **Architecture:** `docs/apps/diagrams.md`: system diagram with decorator placement
