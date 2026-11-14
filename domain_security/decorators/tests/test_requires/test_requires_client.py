"""Tests for requires permission decorator."""

from __future__ import annotations

import pytest

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from domain_security.decorators.requires.requires_client import Requires, requires
from domain_security.errors.security_errors import AuthzError
from domain_security.services.authz.authz_client import Authorizer
from domain_security.services.authz.authz_objects import Permission, PolicyDecision


class TestRequires:
    """Requires permission enforcement decorator."""

    def test_decorator_preserves_function_name(self) -> None:
        """Decorated function retains its name via functools.wraps."""

        @requires("read")
        def get_data() -> str:
            """Get data."""
            return "data"

        assert get_data.__name__ == "get_data"

    def test_decorator_preserves_docstring(self) -> None:
        """Decorated function retains its docstring via functools.wraps."""

        @requires("read")
        def get_data() -> str:
            """Get data from somewhere."""
            return "data"

        assert get_data.__doc__ is not None
        assert "Get data from somewhere" in get_data.__doc__

    def test_decorator_denies_when_context_unset(self) -> None:
        """Decorated function raises AuthzError when context is unset."""

        @requires("read")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        with pytest.raises(AuthzError):
            protected_function()

    def test_decorator_denies_anonymous_context(self) -> None:
        """Decorated function denies access to anonymous principal."""
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=None, tenant_id="tenant:test"))

        @requires("read")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        with pytest.raises(AuthzError):
            protected_function()

    def test_decorator_denies_missing_scope(self) -> None:
        """Decorated function denies when principal lacks required scope."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        with pytest.raises(AuthzError):
            protected_function()

    def test_decorator_allows_with_scope(self) -> None:
        """Decorated function allows when principal has required scope."""
        principal = Principal(
            id="user:reader", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("read")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        result = protected_function()
        assert result == "result"

    def test_decorator_with_custom_authorizer(
        self, always_allow_authorizer: Authorizer
    ) -> None:
        """Requires can be initialized with custom authorizer."""

        @Requires(authorizer=always_allow_authorizer)("read")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        result = protected_function()
        assert result == "result"

    def test_decorator_rejects_denied_permission(
        self, always_deny_authorizer: Authorizer
    ) -> None:
        """Requires with custom authorizer respects deny decision."""
        principal = Principal(
            id="user:test", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @Requires(authorizer=always_deny_authorizer)("read")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        with pytest.raises(AuthzError):
            protected_function()

    def test_decorator_keeps_falsy_custom_authorizer(self) -> None:
        """Requires keeps a custom authorizer even when it evaluates as falsy."""

        class FalsyAllowAuthorizer(Authorizer):
            """Authorizer that allows everything and evaluates as False."""

            def __bool__(self) -> bool:
                """Report the authorizer as falsy."""
                return False

            def check(self, ctx, permission: Permission) -> PolicyDecision:
                """Always allow access."""
                return PolicyDecision(allowed=True)

        @Requires(authorizer=FalsyAllowAuthorizer())("read")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        assert protected_function() == "result"

    def test_module_handle_requires(self) -> None:
        """Module-level requires handle exists and works."""
        principal = Principal(
            id="user:reader", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("read")
        def protected_function() -> str:
            """Do something protected."""
            return "protected"

        result = protected_function()
        assert result == "protected"

    def test_decorator_with_function_args(self) -> None:
        """Decorated function forwards args correctly."""
        principal = Principal(
            id="user:reader", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("read")
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        result = multiply(3, 4)
        assert result == 12

    def test_decorator_with_function_kwargs(self) -> None:
        """Decorated function forwards kwargs correctly."""
        principal = Principal(
            id="user:reader", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("read")
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        result = greet(name="World", greeting="Hi")
        assert result == "Hi, World!"

    def test_decorator_multiple_scopes_allows_any(self) -> None:
        """Decorated function allows if principal has any required scope."""
        principal = Principal(
            id="user:admin",
            roles=frozenset(),
            scopes=frozenset(["read", "write", "delete"]),
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("write")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        result = protected_function()
        assert result == "result"

    def test_decorator_error_preserves_context(self) -> None:
        """Decorator error includes permission in context."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        def protected_function() -> str:
            """Do something protected."""
            return "result"

        with pytest.raises(AuthzError) as exc_info:
            protected_function()
        assert exc_info.value.context["permission"] == "admin"
