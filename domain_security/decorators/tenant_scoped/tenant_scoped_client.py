"""Declarative tenant-boundary enforcement for service methods."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Mapping
from typing import Any, ClassVar

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    SecurityContext,
)
from domain_security.decorators.class_fanout import ClassFanout
from domain_security.decorators.constants import tenant_scoped as const
from domain_security.errors.constants import security_errors as errors_const
from domain_security.errors.security_errors import (
    SecurityDeclarationError,
    TenancyError,
)
from domain_security.services.tenancy.tenancy_client import TenancyGuard

_TENANT_SCOPED_DECORATED_MARKER = "__tenant_scoped_decorated__"


class TenantScoped:
    """Decorator factory enforcing the tenant boundary from the ambient security context."""

    _ANONYMOUS: ClassVar[SecurityContext] = SecurityContext(
        principal=None, tenant_id=None
    )

    def __init__(self, guard: TenancyGuard | None = None) -> None:
        """Store the tenancy guard, defaulting to the standard TenancyGuard."""
        self._guard = guard if guard is not None else TenancyGuard()
        self._contexts = SecurityContextManager()

    def __call__[**Params, Return](
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

    def _decorate_callable[**Params, Return](
        self, func: Callable[Params, Return], param_name: str
    ) -> Callable[Params, Return]:
        """Decorate a single callable."""
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            tenant_id = self._tenant_argument(signature, param_name, args, kwargs)
            self._guard.check(self._current_context(), tenant_id)
            return func(*args, **kwargs)

        setattr(wrapper, _TENANT_SCOPED_DECORATED_MARKER, True)
        return wrapper

    def _decorate_class(self, cls: type, param_name: str) -> type:
        """Apply the decorator to all public methods of a class."""

        def decorate(name: str, func: Callable[..., object]) -> Callable[..., object]:
            self._validate_tenant_param(func, param_name, name)
            return self._decorate_callable(func, param_name)

        return ClassFanout.decorate_class(
            cls, _TENANT_SCOPED_DECORATED_MARKER, decorate
        )

    @staticmethod
    def _validate_tenant_param(
        func: Callable[..., object], param_name: str, method_name: str
    ) -> None:
        """Validate that a method has the tenant parameter at declaration time."""
        if param_name == const.SELF_TENANT_ID:
            return
        if param_name not in inspect.signature(func).parameters:
            raise SecurityDeclarationError(
                message=errors_const.ERR_SECURITY_DECLARATION_FAILED,
                method_name=method_name,
                param_name=param_name,
            )

    @staticmethod
    def _tenant_argument(
        signature: inspect.Signature,
        param_name: str,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> str:
        """Extract the tenant id from the call arguments or the instance attribute."""
        if param_name == const.SELF_TENANT_ID:
            if not args:
                raise TenancyError(message=const.ERR_TENANT_SCOPED_UNBOUND_SELF)
            value = args[0].tenant_id
        else:
            bound = signature.bind(*args, **kwargs)
            if param_name not in bound.arguments:
                raise TenancyError(
                    message=const.ERR_TENANT_SCOPED_PARAM_MISSING,
                    param_name=param_name,
                )
            value = bound.arguments[param_name]
        if value is None:
            raise TenancyError(
                message=const.ERR_TENANT_SCOPED_NULL_TENANT,
                param_name=param_name,
            )
        return str(value)

    def _current_context(self) -> SecurityContext:
        """Return the ambient context, or an anonymous one when unset."""
        current = self._contexts.get()
        return current if current is not None else self._ANONYMOUS


tenant_scoped = TenantScoped()
