"""Declarative permission enforcement for service methods."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

from monitoring_suite.security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from monitoring_suite.security.context.security_context.security_context_objects import (
    SecurityContext,
)
from monitoring_suite.security.services.authz.authz_client import Authorizer
from monitoring_suite.security.services.authz.authz_objects import Permission

_REQUIRES_DECORATED_MARKER = "__requires_decorated__"


class Requires:
    """Decorator factory enforcing a permission from the ambient security context."""

    def __init__(self, authorizer: Authorizer | None = None) -> None:
        """Store the authorizer, defaulting to the scope-based Authorizer."""
        self._authorizer = authorizer or Authorizer()

    def __call__[**Params, Return](
        self,
        permission: str,
    ) -> Callable[[Callable[Params, Return] | type], Callable[Params, Return] | type]:
        """Return a decorator that enforces the permission before each call or on class methods."""

        def decorate(
            target: Callable[Params, Return] | type,
        ) -> Callable[Params, Return] | type:
            if inspect.isclass(target):
                return self._decorate_class(target, permission)
            return self._decorate_callable(target, permission)

        return decorate

    def _decorate_callable[**Params, Return](
        self, function: Callable[Params, Return], permission: str
    ) -> Callable[Params, Return]:
        """Decorate a single callable."""

        @functools.wraps(function)
        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            self._authorizer.require(self._current_context(), Permission(permission))
            return function(*args, **kwargs)

        setattr(wrapper, _REQUIRES_DECORATED_MARKER, True)
        return wrapper

    def _decorate_class(self, cls: type, permission: str) -> type:
        """Apply the decorator to all public methods of a class."""
        for name, method in cls.__dict__.items():
            if self._should_decorate(name, method):
                decorated: Any = self._apply_to_method(method, permission)
                setattr(cls, name, decorated)
        return cls

    @staticmethod
    def _should_decorate(name: str, member: Any) -> bool:
        """Check if an object should be decorated."""
        if name.startswith("_") or inspect.isbuiltin(member):
            return False
        if isinstance(member, property):
            return False
        if inspect.isclass(member):
            return False
        if hasattr(member, _REQUIRES_DECORATED_MARKER):
            return False
        return callable(member) or isinstance(member, (classmethod, staticmethod))

    def _apply_to_method(self, method: Any, permission: str) -> Any:
        """Apply decorator to a method, handling classmethod and staticmethod."""
        if isinstance(method, classmethod):
            return classmethod(self._decorate_callable(method.__func__, permission))
        if isinstance(method, staticmethod):
            return staticmethod(self._decorate_callable(method.__func__, permission))
        return self._decorate_callable(method, permission)

    @staticmethod
    def _current_context() -> SecurityContext:
        """Return the ambient context, or an anonymous one when unset."""
        current = SecurityContextManager().get()
        return current or SecurityContext(principal=None, tenant_id=None)


requires = Requires()
