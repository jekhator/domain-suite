"""Tests for class-level @requires decorator."""

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


class TestRequiresClassLevel:
    """Class-level @requires decorator enforcement."""

    def test_class_decorator_applies_to_all_public_methods(self) -> None:
        """Decorator applied to class wraps all public methods."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with protected methods."""

            def read(self) -> str:
                """Read operation."""
                return "read"

            def write(self) -> str:
                """Write operation."""
                return "write"

        service = Service()
        assert service.read() == "read"
        assert service.write() == "write"

    def test_class_decorator_skips_private_methods(self) -> None:
        """Decorator skips private methods."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with private method."""

            def public_method(self) -> str:
                """Public method."""
                return self._private_method()

            def _private_method(self) -> str:
                """Private method."""
                return "private"

        service = Service()
        assert service.public_method() == "private"

    def test_class_decorator_skips_dunder_methods(self) -> None:
        """Decorator skips dunder methods."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with dunder method."""

            def __init__(self) -> None:
                """Initialize."""
                self.value = "test"

            def __str__(self) -> str:
                """String representation."""
                return self.value

            def public(self) -> str:
                """Public method."""
                return "public"

        service = Service()
        assert service.public() == "public"
        assert str(service) == "test"

    def test_class_decorator_skips_properties(self) -> None:
        """Decorator skips properties."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with property."""

            def __init__(self) -> None:
                """Initialize."""
                self._data = "data"

            @property
            def data(self) -> str:
                """Get data."""
                return self._data

            def get_data(self) -> str:
                """Get data via method."""
                return self.data

        service = Service()
        assert service.get_data() == "data"
        assert service.data == "data"

    def test_class_decorator_handles_classmethod(self) -> None:
        """Decorator handles classmethods correctly."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with classmethod."""

            @classmethod
            def create(cls) -> Service:
                """Create instance."""
                return cls()

        service = Service.create()
        assert isinstance(service, Service)

    def test_class_decorator_handles_staticmethod(self) -> None:
        """Decorator handles staticmethods correctly."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with staticmethod."""

            @staticmethod
            def helper() -> str:
                """Helper static method."""
                return "helper"

        assert Service.helper() == "helper"

    def test_class_decorator_skips_inherited_methods(self) -> None:
        """Decorator applies only to methods in the class dict, not inherited."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        class Base:
            """Base class with method."""

            def base_method(self) -> str:
                """Base method."""
                return "base"

        @requires("admin")
        class Derived(Base):
            """Derived class."""

            def derived_method(self) -> str:
                """Derived method."""
                return "derived"

        derived = Derived()
        assert derived.derived_method() == "derived"
        assert derived.base_method() == "base"

    def test_class_decorator_denies_when_permission_missing(self) -> None:
        """Decorated class methods deny when permission is missing."""
        principal = Principal(
            id="user:reader", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service requiring admin."""

            def admin_op(self) -> str:
                """Admin operation."""
                return "admin"

        service = Service()
        with pytest.raises(AuthzError):
            service.admin_op()

    def test_class_decorator_with_custom_authorizer(
        self, always_allow_authorizer: Authorizer
    ) -> None:
        """Class decorator with custom authorizer allows operation."""

        @Requires(authorizer=always_allow_authorizer)("anything")
        class Service:
            """Service with custom authorizer."""

            def method(self) -> str:
                """Protected method."""
                return "result"

        service = Service()
        assert service.method() == "result"

    def test_class_decorator_method_already_decorated_skipped(self) -> None:
        """Method already decorated with @requires is not re-decorated."""
        principal = Principal(
            id="user:reader", roles=frozenset(), scopes=frozenset(["read"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with mix of decorated and undecorated methods."""

            @requires("read")
            def read_op(self) -> str:
                """Read operation, explicitly requires read."""
                return "read"

            def write_op(self) -> str:
                """Write operation, requires admin from class decorator."""
                return "write"

        service = Service()
        assert service.read_op() == "read"
        with pytest.raises(AuthzError):
            service.write_op()

    def test_class_decorator_forwards_return_values(self) -> None:
        """Class decorator forwards return values correctly."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Service:
            """Service with methods returning different types."""

            def get_int(self) -> int:
                """Get integer."""
                return 42

            def get_dict(self) -> dict[str, str]:
                """Get dictionary."""
                return {"key": "value"}

            def get_list(self) -> list[int]:
                """Get list."""
                return [1, 2, 3]

        service = Service()
        assert service.get_int() == 42
        assert service.get_dict() == {"key": "value"}
        assert service.get_list() == [1, 2, 3]

    def test_class_decorator_with_method_args(self) -> None:
        """Class decorator preserves method arguments."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Calculator:
            """Calculator with protected methods."""

            def add(self, a: int, b: int) -> int:
                """Add two numbers."""
                return a + b

            def multiply(self, a: int, b: int = 2) -> int:
                """Multiply two numbers."""
                return a * b

        calc = Calculator()
        assert calc.add(3, 4) == 7
        assert calc.multiply(5) == 10
        assert calc.multiply(5, 3) == 15

    def test_class_decorator_nested_classes_skipped(self) -> None:
        """Decorator skips nested classes."""
        principal = Principal(
            id="user:admin", roles=frozenset(), scopes=frozenset(["admin"])
        )
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @requires("admin")
        class Outer:
            """Outer class."""

            class Inner:
                """Inner class."""

                def inner_method(self) -> str:
                    """Inner method."""
                    return "inner"

            def outer_method(self) -> str:
                """Outer method."""
                return "outer"

        outer = Outer()
        assert outer.outer_method() == "outer"
        inner = Outer.Inner()
        assert inner.inner_method() == "inner"
