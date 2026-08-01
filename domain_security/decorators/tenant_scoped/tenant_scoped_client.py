"""Declarative tenant-boundary enforcement for service methods."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    SecurityContext,
)
from domain_security.decorators.constants import tenant_scoped as const
from domain_security.errors.constants import security_errors as errors_const
from domain_security.errors.security_errors import (
    SecurityDeclarationError,
    TenancyError,
)
from domain_security.services.tenancy.tenancy_client import TenancyGuard

Params = ParamSpec("Params")
Return = TypeVar("Return")

_TENANT_SCOPED_DECORATED_MARKER = "__tenant_scoped_decorated__"


class TenantScoped:
    """Decorator factory enforcing the tenant boundary from the ambient security context."""

    def __init__(self, guard: TenancyGuard | None = None) -> None:
        """Store the tenancy guard, defaulting to the standard TenancyGuard."""
        self._guard = guard or TenancyGuard()

    def __call__(
        self,
        param_name: str,
    ) -> Callable[[Callable[Params, Return] | type], Callable[Params, Return] | type]:
        """Return a decorator that checks the named tenant argument before each call or on class methods."""

        def decorate(
            target: Callable[Params, Return] | type,
        ) -> Callable[Params, Return] | type:
            if inspect.isclass(target):
                return self._decorate_class(target, param_name)
            return self._decorate_callable(target, param_name)

        return decorate

    def _decorate_callable(
        self, func: Callable[Params, Return], param_name: str
    ) -> Callable[Params, Return]:
        """Decorate a single callable."""

        @functools.wraps(func)
        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            tenant_id = self._tenant_argument(func, param_name, args, kwargs)
            self._guard.check(self._current_context(), tenant_id)
            return func(*args, **kwargs)

        setattr(wrapper, _TENANT_SCOPED_DECORATED_MARKER, True)
        return wrapper

    def _decorate_class(self, cls: type, param_name: str) -> type:
        """Apply the decorator to all public methods of a class."""
        for name, method in cls.__dict__.items():
            if self._should_decorate(name, method):
                self._validate_tenant_param(method, param_name, name)
                decorated: Any = self._apply_to_method(method, param_name)
                setattr(cls, name, decorated)
        return cls

    @staticmethod
    def _should_decorate(name: str, obj: Any) -> bool:
        """Check if an object should be decorated."""
        if name.startswith("_") or inspect.isbuiltin(obj):
            return False
        if isinstance(obj, property):
            return False
        if inspect.isclass(obj):
            return False
        if hasattr(obj, _TENANT_SCOPED_DECORATED_MARKER):
            return False
        return callable(obj) or isinstance(obj, (classmethod, staticmethod))

    def _validate_tenant_param(
        self, method: Any, param_name: str, method_name: str
    ) -> None:
        """Validate that a method has the tenant parameter at declaration time."""
        func = (
            method.__func__
            if isinstance(method, (classmethod, staticmethod))
            else method
        )
        sig = inspect.signature(func)
        if param_name != const.SELF_TENANT_ID:
            if param_name not in sig.parameters:
                raise SecurityDeclarationError(
                    message=errors_const.ERR_SECURITY_DECLARATION_FAILED,
                    method_name=method_name,
                    param_name=param_name,
                )

    def _apply_to_method(
        self, method: Any, param_name: str
    ) -> Callable[Params, Return] | classmethod | staticmethod:
        """Apply decorator to a method, handling classmethod and staticmethod."""
        if isinstance(method, classmethod):
            return classmethod(self._decorate_callable(method.__func__, param_name))
        if isinstance(method, staticmethod):
            return staticmethod(self._decorate_callable(method.__func__, param_name))
        return self._decorate_callable(method, param_name)

    @staticmethod
    def _tenant_argument(
        func: Callable[..., Any],
        param_name: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> str:
        """Extract the tenant id from the call arguments or the instance attribute."""
        if param_name == const.SELF_TENANT_ID:
            if not args:
                raise TenancyError(message=const.ERR_TENANT_SCOPED_UNBOUND_SELF)
            return str(args[0].tenant_id)
        bound = inspect.signature(func).bind(*args, **kwargs)
        if param_name not in bound.arguments:
            raise TenancyError(
                message=const.ERR_TENANT_SCOPED_PARAM_MISSING,
                param_name=param_name,
            )
        return str(bound.arguments[param_name])

    @staticmethod
    def _current_context() -> SecurityContext:
        """Return the ambient context, or an anonymous one when unset."""
        current = SecurityContextManager().get()
        return current or SecurityContext(principal=None, tenant_id=None)


tenant_scoped = TenantScoped()
