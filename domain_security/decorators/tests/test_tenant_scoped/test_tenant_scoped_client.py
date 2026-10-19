"""Tests for tenant_scoped decorator."""

from __future__ import annotations

import pytest

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from domain_security.decorators.constants import tenant_scoped as const
from domain_security.decorators.tenant_scoped.tenant_scoped_client import (
    TenantScoped,
    tenant_scoped,
)
from domain_security.errors.security_errors import TenancyError
from domain_security.services.tenancy.tenancy_client import TenancyGuard


class TestTenantScoped:
    """TenantScoped tenant boundary enforcement decorator."""

    def test_decorator_preserves_function_name(self) -> None:
        """Decorated function retains its name via functools.wraps."""

        @tenant_scoped("tenant_id")
        def get_entity(tenant_id: str) -> str:
            """Get entity."""
            return "entity"

        assert get_entity.__name__ == "get_entity"

    def test_decorator_preserves_docstring(self) -> None:
        """Decorated function retains its docstring via functools.wraps."""

        @tenant_scoped("tenant_id")
        def get_entity(tenant_id: str) -> str:
            """Get entity from somewhere."""
            return "entity"

        assert get_entity.__doc__ is not None
        assert "Get entity from somewhere" in get_entity.__doc__

    def test_decorator_with_kwarg_tenant_id(self) -> None:
        """Decorator extracts tenant_id from kwarg."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        def scoped_function(tenant_id: str) -> str:
            """Do something scoped."""
            return f"scoped to {tenant_id}"

        result = scoped_function(tenant_id="tenant:acme")
        assert result == "scoped to tenant:acme"

    def test_decorator_denies_tenant_mismatch_kwarg(self) -> None:
        """Decorator denies when kwarg tenant differs from context."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        def scoped_function(tenant_id: str) -> str:
            """Do something scoped."""
            return f"scoped to {tenant_id}"

        with pytest.raises(TenancyError):
            scoped_function(tenant_id="tenant:widgets")

    def test_decorator_with_positional_tenant_id(self) -> None:
        """Decorator extracts tenant_id from positional argument."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        def scoped_function(tenant_id: str) -> str:
            """Do something scoped."""
            return f"scoped to {tenant_id}"

        result = scoped_function("tenant:acme")
        assert result == "scoped to tenant:acme"

    def test_decorator_self_tenant_id_from_instance(self) -> None:
        """Decorator extracts tenant_id from self.tenant_id instance attribute."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        class Entity:
            """Entity with tenant scoped method."""

            def __init__(self, tenant_id: str) -> None:
                """Initialize with tenant_id."""
                self.tenant_id = tenant_id

            @tenant_scoped("self.tenant_id")
            def get_data(self) -> str:
                """Get entity data."""
                return f"data for {self.tenant_id}"

        entity = Entity(tenant_id="tenant:acme")
        result = entity.get_data()
        assert result == "data for tenant:acme"

    def test_decorator_self_tenant_id_denies_mismatch(self) -> None:
        """Decorator denies when self.tenant_id differs from context."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        class Entity:
            """Entity with tenant scoped method."""

            def __init__(self, tenant_id: str) -> None:
                """Initialize with tenant_id."""
                self.tenant_id = tenant_id

            @tenant_scoped("self.tenant_id")
            def get_data(self) -> str:
                """Get entity data."""
                return f"data for {self.tenant_id}"

        entity = Entity(tenant_id="tenant:widgets")
        with pytest.raises(TenancyError):
            entity.get_data()

    def test_decorator_self_tenant_id_requires_bound_call(self) -> None:
        """Decorator raises when self.tenant_id used without instance."""

        @tenant_scoped("self.tenant_id")
        def unbound_function() -> str:
            """Unbound function."""
            return "should fail"

        with pytest.raises(TenancyError) as exc_info:
            unbound_function()
        assert exc_info.value.message == const.ERR_TENANT_SCOPED_UNBOUND_SELF

    def test_decorator_rejects_none_tenant_argument(self) -> None:
        """Decorator refuses a None tenant argument even when the context tenant is the string None."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="None"))

        @tenant_scoped("tenant_id")
        def scoped_function(tenant_id: str | None) -> str:
            """Scoped function accepting an optional tenant."""
            return f"scoped to {tenant_id}"

        with pytest.raises(TenancyError) as exc_info:
            scoped_function(tenant_id=None)
        assert exc_info.value.message == const.ERR_TENANT_SCOPED_NULL_TENANT

    def test_decorator_self_tenant_id_none_raises(self) -> None:
        """Decorator refuses an instance whose tenant_id attribute is None."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="None"))

        class Entity:
            """Entity whose tenant is unset."""

            def __init__(self) -> None:
                """Leave tenant_id unset."""
                self.tenant_id = None

            @tenant_scoped("self.tenant_id")
            def get_data(self) -> str:
                """Get entity data."""
                return "data"

        with pytest.raises(TenancyError) as exc_info:
            Entity().get_data()
        assert exc_info.value.message == const.ERR_TENANT_SCOPED_NULL_TENANT

    def test_decorator_missing_tenant_parameter(self) -> None:
        """Decorator raises when function lacks the tenant parameter."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("missing_param")
        def scoped_function() -> str:
            """Missing the tenant parameter."""
            return "result"

        with pytest.raises(TenancyError) as exc_info:
            scoped_function()
        assert exc_info.value.message == const.ERR_TENANT_SCOPED_PARAM_MISSING

    def test_decorator_denies_when_context_unset(self) -> None:
        """Decorator denies when security context is unset."""

        @tenant_scoped("tenant_id")
        def scoped_function(tenant_id: str) -> str:
            """Scoped to tenant."""
            return f"scoped to {tenant_id}"

        with pytest.raises(TenancyError):
            scoped_function(tenant_id="tenant:any")

    def test_decorator_with_custom_guard(self) -> None:
        """TenantScoped can be initialized with custom guard."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        custom_guard = TenancyGuard()

        @TenantScoped(guard=custom_guard)("tenant_id")
        def scoped_function(tenant_id: str) -> str:
            """Scoped to tenant."""
            return f"scoped to {tenant_id}"

        result = scoped_function(tenant_id="tenant:acme")
        assert result == "scoped to tenant:acme"

    def test_module_handle_tenant_scoped(self) -> None:
        """Module-level tenant_scoped handle exists and works."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @tenant_scoped("tenant_id")
        def scoped_function(tenant_id: str) -> str:
            """Scoped function."""
            return f"scoped to {tenant_id}"

        result = scoped_function(tenant_id="tenant:test")
        assert result == "scoped to tenant:test"

    def test_decorator_with_multiple_args(self) -> None:
        """Decorator handles functions with multiple arguments."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        def process(tenant_id: str, operation: str, data: dict) -> str:
            """Process with tenant_id."""
            return f"{tenant_id}:{operation}"

        result = process("tenant:acme", "read", {"key": "value"})
        assert result == "tenant:acme:read"

    def test_decorator_forwards_return_value(self) -> None:
        """Decorator forwards the decorated function return value."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:test"))

        @tenant_scoped("tenant_id")
        def get_tenant_config(tenant_id: str) -> dict:
            """Get configuration."""
            return {"tenant": tenant_id, "name": "Test"}

        result = get_tenant_config(tenant_id="tenant:test")
        assert result == {"tenant": "tenant:test", "name": "Test"}

    def test_decorator_error_includes_param_name(self) -> None:
        """Decorator error includes the param_name in context."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("workspace_id")
        def scoped_function(other_id: str) -> str:
            """Missing workspace_id param."""
            return "result"

        with pytest.raises(TenancyError) as exc_info:
            scoped_function(other_id="value")
        param_name_val = exc_info.value.context.get("param_name", "")
        assert isinstance(param_name_val, str)
        assert "workspace_id" in param_name_val
