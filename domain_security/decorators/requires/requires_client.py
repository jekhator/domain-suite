"""Declarative permission enforcement for service methods."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import ClassVar

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    SecurityContext,
)
from domain_security.decorators.class_fanout import ClassFanout
from domain_security.services.authz.authz_client import Authorizer
from domain_security.services.authz.authz_objects import Permission

_REQUIRES_DECORATED_MARKER = "__requires_decorated__"


class Requires:
    """Decorator factory enforcing a permission from the ambient security context."""

    _ANONYMOUS: ClassVar[SecurityContext] = SecurityContext(
        principal=None, tenant_id=None
    )

    def __init__(self, authorizer: Authorizer | None = None) -> None:
        """Store the authorizer, defaulting to the scope-based Authorizer."""
        self._authorizer = authorizer if authorizer is not None else Authorizer()
        self._contexts = SecurityContextManager()

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
        self, func: Callable[Params, Return], permission: str
    ) -> Callable[Params, Return]:
        """Decorate a single callable."""
        required = Permission(permission)

        @functools.wraps(func)
        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            self._authorizer.require(self._current_context(), required)
            return func(*args, **kwargs)

        setattr(wrapper, _REQUIRES_DECORATED_MARKER, True)
        return wrapper

    def _decorate_class(self, cls: type, permission: str) -> type:
        """Apply the decorator to all public methods of a class."""
        return ClassFanout.decorate_class(
            cls,
            _REQUIRES_DECORATED_MARKER,
            lambda _name, func: self._decorate_callable(func, permission),
        )

    def _current_context(self) -> SecurityContext:
        """Return the ambient context, or an anonymous one when unset."""
        current = self._contexts.get()
        return current if current is not None else self._ANONYMOUS


requires = Requires()
