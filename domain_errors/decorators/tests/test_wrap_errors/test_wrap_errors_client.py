"""Tests for the wrap_errors decorator."""

from __future__ import annotations

import asyncio
import inspect

import pytest

from domain_errors.decorators.wrap_errors.wrap_errors_client import (
    WrapErrorsClient,
    wrap_errors,
)
from domain_errors.domains.domain_error.domain_error import DomainError


class DemoError(DomainError):
    """Demo DomainError subclass for testing."""

    code = "DEMO_ERROR"
    domain = "test"


class TestWrapErrorsSyncHappyPath:
    """Tests for sync functions with no exception raised."""

    def test_sync_function_returns_value_unchanged(self) -> None:
        """Sync function returns its value when nothing raises."""

        @wrap_errors(DemoError)
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_sync_function_with_no_args_returns_value(self) -> None:
        """Sync function with no args returns its value."""

        @wrap_errors(DemoError)
        def get_constant() -> str:
            return "hello"

        result = get_constant()
        assert result == "hello"

    def test_sync_function_with_kwargs_returns_value(self) -> None:
        """Sync function with keyword-only args returns its value."""

        @wrap_errors(DemoError)
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}"

        result = greet("Alice", greeting="Hi")
        assert result == "Hi, Alice"


class TestWrapErrorsSyncWrap:
    """Tests for sync functions with exception wrapping."""

    def test_sync_caught_exception_wrapped_into_domain_error(self) -> None:
        """Caught exception is wrapped into the target DomainError."""

        @wrap_errors(DemoError)
        def divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(DemoError):
            divide(10, 0)

    def test_sync_wrapped_error_has_original_as_cause(self) -> None:
        """Wrapped DomainError has the original exception as __cause__."""

        @wrap_errors(DemoError)
        def divide(a: int, b: int) -> float:
            return a / b

        try:
            divide(10, 0)
        except DemoError as error:
            assert isinstance(error.__cause__, ZeroDivisionError)

    def test_sync_custom_message_passes_through(self) -> None:
        """Custom message parameter is stored in the DomainError."""

        @wrap_errors(DemoError, message="Custom error message")
        def fail() -> None:
            raise ValueError("original error")

        with pytest.raises(DemoError) as exc_info:
            fail()
        assert exc_info.value.message == "Custom error message"

    def test_sync_captured_args_in_context(self) -> None:
        """Function arguments are captured in the DomainError context."""

        @wrap_errors(DemoError)
        def divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(DemoError) as exc_info:
            divide(10, 0)
        assert exc_info.value.context == {"a": 10, "b": 0}

    def test_sync_captured_args_with_defaults(self) -> None:
        """Default parameter values appear in captured context."""

        @wrap_errors(DemoError)
        def process(value: int, factor: int = 2) -> int:
            raise ValueError("always fails")

        with pytest.raises(DemoError) as exc_info:
            process(5)
        assert exc_info.value.context == {"value": 5, "factor": 2}

    def test_sync_catch_narrowing_non_matching_exception_passes_raw(self) -> None:
        """Exception not in catch tuple propagates unwrapped."""

        @wrap_errors(DemoError, catch=(ValueError,))
        def fail() -> None:
            raise KeyError("not caught")

        with pytest.raises(KeyError) as exc_info:
            fail()
        assert not isinstance(exc_info.value, DemoError)


class TestWrapErrorsAsyncHappyPath:
    """Tests for async functions with no exception raised."""

    def test_async_function_returns_value_unchanged(self) -> None:
        """Async function returns its value when nothing raises."""

        @wrap_errors(DemoError)
        async def async_add(a: int, b: int) -> int:
            return a + b

        result = asyncio.run(async_add(2, 3))
        assert result == 5

    def test_async_function_with_no_args_returns_value(self) -> None:
        """Async function with no args returns its value."""

        @wrap_errors(DemoError)
        async def async_get_constant() -> str:
            return "hello"

        result = asyncio.run(async_get_constant())
        assert result == "hello"

    def test_async_function_with_kwargs_returns_value(self) -> None:
        """Async function with keyword-only args returns its value."""

        @wrap_errors(DemoError)
        async def async_greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}"

        result = asyncio.run(async_greet("Bob", greeting="Greetings"))
        assert result == "Greetings, Bob"


class TestWrapErrorsAsyncWrap:
    """Tests for async functions with exception wrapping."""

    def test_async_caught_exception_wrapped_into_domain_error(self) -> None:
        """Async caught exception is wrapped into the target DomainError."""

        @wrap_errors(DemoError)
        async def async_divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(DemoError):
            asyncio.run(async_divide(10, 0))

    def test_async_wrapped_error_has_original_as_cause(self) -> None:
        """Async wrapped DomainError has the original exception as __cause__."""

        @wrap_errors(DemoError)
        async def async_divide(a: int, b: int) -> float:
            return a / b

        try:
            asyncio.run(async_divide(10, 0))
        except DemoError as error:
            assert isinstance(error.__cause__, ZeroDivisionError)

    def test_async_custom_message_passes_through(self) -> None:
        """Async custom message parameter is stored in the DomainError."""

        @wrap_errors(DemoError, message="Async custom message")
        async def async_fail() -> None:
            raise ValueError("original error")

        with pytest.raises(DemoError) as exc_info:
            asyncio.run(async_fail())
        assert exc_info.value.message == "Async custom message"

    def test_async_captured_args_in_context(self) -> None:
        """Async function arguments are captured in the DomainError context."""

        @wrap_errors(DemoError)
        async def async_divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(DemoError) as exc_info:
            asyncio.run(async_divide(10, 0))
        assert exc_info.value.context == {"a": 10, "b": 0}


class TestWrapErrorsDomainErrorPassthrough:
    """Tests for DomainError pass-through behavior."""

    def test_sync_domain_error_passes_through_unwrapped(self) -> None:
        """DomainError (or subclass) is not re-wrapped in sync context."""

        class CustomError(DemoError):
            pass

        @wrap_errors(DemoError)
        def fail_with_domain_error() -> None:
            raise CustomError(message="original domain error")

        with pytest.raises(CustomError) as exc_info:
            fail_with_domain_error()
        # Verify it's the same instance, not wrapped
        assert exc_info.value.__cause__ is None
        assert exc_info.value.message == "original domain error"

    def test_async_domain_error_passes_through_unwrapped(self) -> None:
        """DomainError (or subclass) is not re-wrapped in async context."""

        class CustomError(DemoError):
            pass

        @wrap_errors(DemoError)
        async def async_fail_with_domain_error() -> None:
            raise CustomError(message="original domain error")

        with pytest.raises(CustomError) as exc_info:
            asyncio.run(async_fail_with_domain_error())
        # Verify it's the same instance, not wrapped
        assert exc_info.value.__cause__ is None
        assert exc_info.value.message == "original domain error"


class TestWrapErrorsCaptureControl:
    """Tests for capture=False and capture-default behavior."""

    def test_capture_false_empty_context(self) -> None:
        """capture=False results in empty context dict."""

        @wrap_errors(DemoError, capture=False)
        def divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(DemoError) as exc_info:
            divide(10, 0)
        assert exc_info.value.context == {}

    def test_capture_false_sync_with_defaults_still_empty(self) -> None:
        """capture=False keeps context empty even when defaults exist."""

        @wrap_errors(DemoError, capture=False)
        def process(value: int, factor: int = 2) -> int:
            raise ValueError("always fails")

        with pytest.raises(DemoError) as exc_info:
            process(5)
        assert exc_info.value.context == {}

    def test_capture_true_default_includes_defaults(self) -> None:
        """capture=True (default) includes default parameter values in context."""

        @wrap_errors(DemoError)
        def process(value: int, factor: int = 2) -> int:
            raise ValueError("always fails")

        with pytest.raises(DemoError) as exc_info:
            process(5)
        assert "factor" in exc_info.value.context
        assert exc_info.value.context["factor"] == 2


class TestWrapErrorsFunctoolsWraps:
    """Tests for functools.wraps preservation of metadata."""

    def test_sync_wrapper_preserves_name(self) -> None:
        """Sync wrapper preserves the original function's __name__."""

        @wrap_errors(DemoError)
        def my_function() -> int:
            return 42

        assert my_function.__name__ == "my_function"

    def test_sync_wrapper_preserves_docstring(self) -> None:
        """Sync wrapper preserves the original function's __doc__."""

        @wrap_errors(DemoError)
        def documented_function() -> int:
            """This is a documented function."""
            return 42

        assert documented_function.__doc__ == "This is a documented function."

    def test_async_wrapper_preserves_name(self) -> None:
        """Async wrapper preserves the original async function's __name__."""

        @wrap_errors(DemoError)
        async def my_async_function() -> int:
            return 42

        assert my_async_function.__name__ == "my_async_function"

    def test_async_wrapper_preserves_docstring(self) -> None:
        """Async wrapper preserves the original async function's __doc__."""

        @wrap_errors(DemoError)
        async def documented_async_function() -> int:
            """This is a documented async function."""
            return 42

        assert (
            documented_async_function.__doc__ == "This is a documented async function."
        )


class TestWrapErrorsModuleLevelFactory:
    """Tests for the module-level wrap_errors factory."""

    def test_wrap_errors_is_for_target(self) -> None:
        """Module-level wrap_errors equals WrapErrorsClient.for_target."""
        assert wrap_errors == WrapErrorsClient.for_target

    def test_wrap_errors_factory_creates_client(self) -> None:
        """wrap_errors(DemoError) returns a WrapErrorsClient instance."""
        client = wrap_errors(DemoError)
        assert isinstance(client, WrapErrorsClient)

    def test_wrap_errors_factory_with_all_params(self) -> None:
        """wrap_errors factory accepts all constructor parameters."""
        client = wrap_errors(
            DemoError,
            catch=(ValueError, KeyError),
            message="factory message",
            capture=False,
        )
        assert client.as_ is DemoError
        assert client.catch == (ValueError, KeyError)
        assert client.message == "factory message"
        assert client.capture is False


class TestWrapErrorsClientDirect:
    """Tests for direct WrapErrorsClient instantiation and usage."""

    def test_client_for_target_classmethod_creates_instance(self) -> None:
        """WrapErrorsClient.for_target creates a properly initialized instance."""
        client = WrapErrorsClient.for_target(DemoError)
        assert client.as_ is DemoError
        assert client.catch == (Exception,)
        assert client.message is None
        assert client.capture is True

    def test_client_call_on_sync_function(self) -> None:
        """WrapErrorsClient instance is callable on sync functions."""

        client = WrapErrorsClient.for_target(DemoError)

        def original_func(x: int) -> int:
            return x * 2

        decorated = client(original_func)
        assert decorated(5) == 10

    def test_client_call_on_async_function(self) -> None:
        """WrapErrorsClient instance is callable on async functions."""

        client = WrapErrorsClient.for_target(DemoError)

        async def original_async_func(x: int) -> int:
            return x * 2

        decorated = client(original_async_func)
        result = asyncio.run(decorated(5))
        assert result == 10

    def test_client_is_frozen(self) -> None:
        """WrapErrorsClient is frozen and cannot be mutated."""
        client = WrapErrorsClient.for_target(DemoError)
        with pytest.raises(AttributeError):
            client.as_ = ValueError  # type: ignore

    def test_client_is_dataclass(self) -> None:
        """WrapErrorsClient is a dataclass with slots."""
        # Verify slots behavior: __slots__ should exist (frozen dataclass with slots)
        assert hasattr(WrapErrorsClient, "__slots__")


class TestWrapErrorsDetectsCoroutineFunction:
    """Tests for correct detection of async vs sync functions."""

    def test_sync_function_not_detected_as_coroutine(self) -> None:
        """Sync function is correctly identified as non-coroutine."""

        def sync_func() -> int:
            return 42

        assert not inspect.iscoroutinefunction(sync_func)

    def test_async_function_detected_as_coroutine(self) -> None:
        """Async function is correctly identified as coroutine."""

        async def async_func() -> int:
            return 42

        assert inspect.iscoroutinefunction(async_func)

    def test_wrapped_sync_function_not_detected_as_coroutine(self) -> None:
        """Wrapped sync function is not detected as coroutine."""

        @wrap_errors(DemoError)
        def sync_func() -> int:
            return 42

        assert not inspect.iscoroutinefunction(sync_func)

    def test_wrapped_async_function_detected_as_coroutine(self) -> None:
        """Wrapped async function is correctly detected as coroutine."""

        @wrap_errors(DemoError)
        async def async_func() -> int:
            return 42

        assert inspect.iscoroutinefunction(async_func)


class TestWrapErrorsSignatureBinding:
    """Tests for inspect.signature binding and apply_defaults."""

    def test_positional_args_captured(self) -> None:
        """Positional arguments are captured by name."""

        @wrap_errors(DemoError)
        def func(a: int, b: int, c: int) -> None:
            raise ValueError("fail")

        with pytest.raises(DemoError) as exc_info:
            func(1, 2, 3)
        assert exc_info.value.context == {"a": 1, "b": 2, "c": 3}

    def test_keyword_args_captured(self) -> None:
        """Keyword-only arguments are captured by name."""

        @wrap_errors(DemoError)
        def func(a: int, *, b: int, c: int) -> None:
            raise ValueError("fail")

        with pytest.raises(DemoError) as exc_info:
            func(1, b=2, c=3)
        assert exc_info.value.context == {"a": 1, "b": 2, "c": 3}

    def test_mixed_args_and_kwargs_captured(self) -> None:
        """Both positional and keyword arguments are captured."""

        @wrap_errors(DemoError)
        def func(a: int, b: int = 10, c: int = 20) -> None:
            raise ValueError("fail")

        with pytest.raises(DemoError) as exc_info:
            func(1, c=30)
        # apply_defaults fills in b=10
        assert exc_info.value.context == {"a": 1, "b": 10, "c": 30}

    def test_no_args_function_captured(self) -> None:
        """Function with no args has empty context (when capture=True)."""

        @wrap_errors(DemoError)
        def func() -> None:
            raise ValueError("fail")

        with pytest.raises(DemoError) as exc_info:
            func()
        assert exc_info.value.context == {}


class TestWrapErrorsCatchTupleVariations:
    """Tests for various catch tuple configurations."""

    def test_default_catch_all_exceptions(self) -> None:
        """Default catch=(Exception,) catches all Exception subclasses."""

        @wrap_errors(DemoError)
        def fail() -> None:
            raise RuntimeError("unexpected")

        with pytest.raises(DemoError):
            fail()

    def test_catch_multiple_specific_exceptions(self) -> None:
        """catch with multiple exception types catches all of them."""

        @wrap_errors(DemoError, catch=(ValueError, KeyError))
        def fail_value() -> None:
            raise ValueError("value error")

        @wrap_errors(DemoError, catch=(ValueError, KeyError))
        def fail_key() -> None:
            raise KeyError("key error")

        with pytest.raises(DemoError):
            fail_value()
        with pytest.raises(DemoError):
            fail_key()

    def test_catch_does_not_catch_base_exception(self) -> None:
        """Exceptions outside catch tuple are not wrapped."""

        @wrap_errors(DemoError, catch=(ValueError,))
        def fail() -> None:
            raise RuntimeError("runtime error")

        with pytest.raises(RuntimeError) as exc_info:
            fail()
        assert not isinstance(exc_info.value, DemoError)


class TestWrapErrorsMessageNone:
    """Tests for None message parameter behavior."""

    def test_none_message_uses_default_message(self) -> None:
        """message=None results in DomainError using its default_message."""

        @wrap_errors(DemoError, message=None)
        def fail() -> None:
            raise ValueError("original")

        with pytest.raises(DemoError) as exc_info:
            fail()
        # DemoError.default_message is the default value
        assert exc_info.value.message == DemoError.default_message


class TestWrapErrorsClassLevel:
    """Tests for class-level @wrap_errors decoration."""

    def test_class_decorator_applied(self) -> None:
        """Applying @wrap_errors to a class decorates all public methods."""

        @wrap_errors(DemoError)
        class ServiceClass:
            def sync_method(self, x: int) -> int:
                if x < 0:
                    raise ValueError("negative")
                return x * 2

            async def async_method(self, x: int) -> int:
                if x < 0:
                    raise ValueError("negative")
                return x * 2

        service = ServiceClass()
        assert service.sync_method(5) == 10

        try:
            service.sync_method(-1)
        except DemoError as error:
            assert isinstance(error.__cause__, ValueError)

    def test_class_async_method_wrapped(self) -> None:
        """Async methods in a decorated class are wrapped with async wrapper."""

        @wrap_errors(DemoError)
        class AsyncService:
            async def fetch(self, url: str) -> str:
                if not url:
                    raise ValueError("empty url")
                return f"data from {url}"

        service = AsyncService()
        result = asyncio.run(service.fetch("example.com"))
        assert result == "data from example.com"

        with pytest.raises(DemoError):
            asyncio.run(service.fetch(""))

    def test_class_skips_private_methods(self) -> None:
        """Private methods (_-prefixed) are not decorated."""

        @wrap_errors(DemoError)
        class ServiceWithPrivate:
            def public_method(self, x: int) -> int:
                return self._private_method(x)

            def _private_method(self, x: int) -> int:
                raise ValueError("private error")

        service = ServiceWithPrivate()

        try:
            service.public_method(1)
        except DemoError:
            pass

        with pytest.raises(ValueError):
            service._private_method(1)

    def test_class_skips_dunder_methods(self) -> None:
        """Dunder methods are not decorated."""

        @wrap_errors(DemoError)
        class ServiceWithDunder:
            def __init__(self) -> None:
                self.value = 0

            def process(self, x: int) -> int:
                return x + self.value

        service = ServiceWithDunder()
        assert service.process(5) == 5

    def test_class_skips_properties(self) -> None:
        """Properties are not decorated."""

        @wrap_errors(DemoError)
        class ServiceWithProperty:
            def __init__(self) -> None:
                self._value = 42

            @property
            def value(self) -> int:
                return self._value

            def get_value(self) -> int:
                return self._value

        service = ServiceWithProperty()
        assert service.value == 42
        assert service.get_value() == 42

    def test_class_skips_nested_classes(self) -> None:
        """Nested classes are not decorated."""

        @wrap_errors(DemoError)
        class ServiceWithNested:
            class NestedClass:
                def fail(self) -> None:
                    raise ValueError("nested error")

            def process(self) -> None:
                raise ValueError("outer error")

        service = ServiceWithNested()

        with pytest.raises(DemoError):
            service.process()

        nested = ServiceWithNested.NestedClass()
        with pytest.raises(ValueError):
            nested.fail()

    def test_class_preserves_staticmethod(self) -> None:
        """Static methods are unwrapped, decorated, and rewrapped."""

        @wrap_errors(DemoError)
        class ServiceWithStatic:
            @staticmethod
            def static_func(x: int) -> int:
                if x < 0:
                    raise ValueError("negative")
                return x * 2

        assert ServiceWithStatic.static_func(5) == 10

        with pytest.raises(DemoError):
            ServiceWithStatic.static_func(-1)

    def test_class_preserves_classmethod(self) -> None:
        """Class methods are unwrapped, decorated, and rewrapped."""

        @wrap_errors(DemoError)
        class ServiceWithClass:
            count = 0

            @classmethod
            def increment(cls, amount: int) -> int:
                if amount < 0:
                    raise ValueError("negative")
                cls.count += amount
                return cls.count

        assert ServiceWithClass.increment(5) == 5

        with pytest.raises(DemoError):
            ServiceWithClass.increment(-1)

    def test_class_respects_capture_false(self) -> None:
        """capture=False applies to all methods in a decorated class."""

        @wrap_errors(DemoError, capture=False)
        class ServiceNoCopy:
            def process(self, secret: str) -> str:
                raise ValueError("error")

        service = ServiceNoCopy()

        with pytest.raises(DemoError) as exc_info:
            service.process("my-secret")
        assert exc_info.value.context == {}

    def test_class_respects_custom_message(self) -> None:
        """message parameter applies to all methods in a decorated class."""

        @wrap_errors(DemoError, message="Custom class error")
        class ServiceMessage:
            def fail(self) -> None:
                raise ValueError("inner")

        service = ServiceMessage()

        with pytest.raises(DemoError) as exc_info:
            service.fail()
        assert exc_info.value.message == "Custom class error"

    def test_class_respects_narrowed_catch(self) -> None:
        """catch parameter applies to all methods in a decorated class."""

        @wrap_errors(DemoError, catch=(ValueError,))
        class ServiceNarrow:
            def fail_value(self) -> None:
                raise ValueError("value error")

            def fail_key(self) -> None:
                raise KeyError("key error")

        service = ServiceNarrow()

        with pytest.raises(DemoError):
            service.fail_value()

        with pytest.raises(KeyError):
            service.fail_key()

    def test_class_skips_already_decorated_methods(self) -> None:
        """Methods already decorated with @wrap_errors are left untouched."""

        class CustomError(DomainError):
            code = "custom_error"
            domain = "test"

        @wrap_errors(DemoError)
        class ServiceMixed:
            @wrap_errors(CustomError)
            def custom_wrapped(self, x: int) -> int:
                raise ValueError("error")

            def normal_method(self, x: int) -> int:
                raise ValueError("error")

        service = ServiceMixed()

        with pytest.raises(CustomError):
            service.custom_wrapped(1)

        with pytest.raises(DemoError):
            service.normal_method(1)

    def test_class_with_mixed_sync_async(self) -> None:
        """Class with both sync and async methods preserves dispatch."""

        @wrap_errors(DemoError)
        class MixedService:
            def sync_add(self, a: int, b: int) -> int:
                if b == 0:
                    raise ValueError("b is zero")
                return a + b

            async def async_add(self, a: int, b: int) -> int:
                if b == 0:
                    raise ValueError("b is zero")
                return a + b

            async def async_multi(self, a: int, b: int, c: int) -> int:
                if c == 0:
                    raise ValueError("c is zero")
                return a + b + c

        service = MixedService()

        assert service.sync_add(2, 3) == 5
        with pytest.raises(DemoError):
            service.sync_add(2, 0)

        result = asyncio.run(service.async_add(2, 3))
        assert result == 5
        with pytest.raises(DemoError):
            asyncio.run(service.async_add(2, 0))

        result = asyncio.run(service.async_multi(2, 3, 4))
        assert result == 9
        with pytest.raises(DemoError):
            asyncio.run(service.async_multi(2, 3, 0))

    def test_class_frozen_dataclass(self) -> None:
        """Class decorator works on frozen dataclasses with slots."""
        from dataclasses import dataclass

        @wrap_errors(DemoError)
        @dataclass(frozen=True, slots=True)
        class DataConfig:
            value: int

            def process(self, x: int) -> int:
                if self.value + x < 0:
                    raise ValueError("negative result")
                return self.value + x

            async def async_process(self, x: int) -> int:
                if self.value + x < 0:
                    raise ValueError("negative result")
                return self.value + x

        config = DataConfig(value=10)
        assert config.process(5) == 15

        with pytest.raises(DemoError) as exc_info:
            config.process(-20)
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert exc_info.value.context == {"x": -20}

        result = asyncio.run(config.async_process(5))
        assert result == 15

        with pytest.raises(DemoError):
            asyncio.run(config.async_process(-20))

    def test_class_causation_chain(self) -> None:
        """Class-decorated methods chain exceptions correctly."""

        @wrap_errors(DemoError)
        class ChainService:
            def fail(self) -> None:
                try:
                    raise KeyError("key error")
                except KeyError as error:
                    raise ValueError("wrapped key error") from error

        service = ChainService()

        with pytest.raises(DemoError) as exc_info:
            service.fail()

        assert isinstance(exc_info.value.__cause__, ValueError)
        assert isinstance(exc_info.value.__cause__.__cause__, KeyError)

    def test_class_decorated_method_preserves_name(self) -> None:
        """Decorated methods in a class preserve __name__."""

        @wrap_errors(DemoError)
        class NamedService:
            def my_method(self) -> str:
                return "test"

        assert NamedService.my_method.__name__ == "my_method"

    def test_class_returns_same_class(self) -> None:
        """Decorating a class returns the same class object (in-place modification)."""

        class MyClass:
            def method(self) -> int:
                return 42

        decorated = wrap_errors(DemoError)(MyClass)
        assert decorated is MyClass

    def test_class_non_callable_raises_type_error(self) -> None:
        """Non-class, non-callable targets raise TypeError."""
        client = WrapErrorsClient.for_target(DemoError)

        with pytest.raises(
            TypeError, match=r"@wrap_errors target must be class or callable"
        ):
            client(42)
