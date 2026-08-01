"""@wrap_errors: wrap a fallible callable's errors into a DomainError via ErrorChain."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar, cast

from domain_errors.domains.domain_error.domain_error import DomainError
from domain_errors.services.chain.chain_client import ErrorChain

Params = ParamSpec("Params")
Return = TypeVar("Return")

WRAP_ERRORS_MARKER = "__wrap_errors_applied__"


@dataclass(frozen=True, slots=True)
class WrapErrorsClient:
    """Wrap errors into target DomainError; DomainError instances pass through."""

    as_: type[DomainError]
    catch: tuple[type[Exception], ...]
    message: str | None
    capture: bool

    @classmethod
    def for_target(
        cls,
        as_: type[DomainError],
        *,
        catch: tuple[type[Exception], ...] = (Exception,),
        message: str | None = None,
        capture: bool = True,
    ) -> WrapErrorsClient:
        """Build a wrap_errors decorator targeting the given DomainError type."""
        return cls(as_=as_, catch=catch, message=message, capture=capture)

    def __call__(self, target: Any) -> Any:
        """Wrap target (callable or class) so caught errors become a DomainError.

        On a callable: applies the decorator directly (sync + async support).
        On a class: fans out over public callables, preserving sync/async dispatch.
        DomainError instances pass through unchanged.
        Raises TypeError if target is neither class nor callable.
        """
        if inspect.isclass(target):
            return self._decorate_class(target)
        if callable(target):
            return self._decorate_callable(target)
        msg = (
            f"@wrap_errors target must be class or callable, "
            f"got {type(target).__name__}"
        )
        raise TypeError(msg)

    def _decorate_callable(
        self, func: Callable[Params, Return]
    ) -> Callable[Params, Return]:
        """Wrap a single callable (function or method)."""
        if inspect.iscoroutinefunction(func):
            async_func = cast("Callable[Params, Awaitable[Any]]", func)

            @functools.wraps(func)
            async def async_wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Any:
                try:
                    return await async_func(*args, **kwargs)
                except DomainError:
                    raise
                except self.catch as error:
                    raise self._as_domain(error, func, args, kwargs) from error

            setattr(async_wrapper, WRAP_ERRORS_MARKER, True)
            return cast("Callable[Params, Return]", async_wrapper)

        @functools.wraps(func)
        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            try:
                return func(*args, **kwargs)
            except DomainError:
                raise
            except self.catch as error:
                raise self._as_domain(error, func, args, kwargs) from error

        setattr(wrapper, WRAP_ERRORS_MARKER, True)
        return wrapper

    def _decorate_class(self, cls: type[Any]) -> type[Any]:
        """Fan out @wrap_errors over all public callables in the class.

        Rules:
        - Only callables in cls.__dict__ (not inherited)
        - Skip: _-prefixed, dunders, properties, nested classes
        - Preserve: classmethod/staticmethod via unwrap/rewrap
        - Override: methods already marked with WRAP_ERRORS_MARKER are left untouched
        - Config: catch, as_, message, capture applied uniformly to each method
        """
        for name, method in list(cls.__dict__.items()):
            if name.startswith("_"):
                continue
            if isinstance(method, property):
                continue
            if isinstance(method, type):
                continue

            is_classmethod = isinstance(method, classmethod)
            is_staticmethod = isinstance(method, staticmethod)

            if is_classmethod or is_staticmethod:
                unwrapped = method.__func__
            else:
                unwrapped = method

            if not callable(unwrapped):
                continue

            if hasattr(unwrapped, WRAP_ERRORS_MARKER):
                continue

            decorated = self._decorate_callable(unwrapped)

            if is_classmethod:
                setattr(cls, name, classmethod(decorated))
            elif is_staticmethod:
                setattr(cls, name, staticmethod(decorated))
            else:
                setattr(cls, name, decorated)

        return cls

    def _as_domain(
        self,
        error: Exception,
        func: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> DomainError:
        """Wrap error into target DomainError with captured call context."""
        return ErrorChain.wrap(
            error,
            as_=self.as_,
            message=self.message,
            **self._capture(func, args, kwargs),
        )

    def _capture(
        self,
        func: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Bind call args to parameter names; empty when capture is off."""
        if not self.capture:
            return {}
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        context = dict(bound.arguments)
        context.pop("self", None)
        context.pop("cls", None)
        return context


wrap_errors = WrapErrorsClient.for_target
