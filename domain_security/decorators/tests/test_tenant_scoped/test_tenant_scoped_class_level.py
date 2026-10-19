"""Tests for class-level @tenant_scoped decorator."""

from __future__ import annotations

import pytest

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from domain_security.decorators.tenant_scoped.tenant_scoped_client import tenant_scoped
from domain_security.errors.security_errors import (
    SecurityDeclarationError,
    TenancyError,
)


class TestTenantScopedClassLevel:
    """Class-level @tenant_scoped decorator enforcement."""

    def test_class_decorator_applies_to_all_public_methods(self) -> None:
        """Decorator applied to class wraps all public methods."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Repository with tenant-scoped methods."""

            def get(self, tenant_id: str) -> str:
                """Get entity."""
                return f"entity for {tenant_id}"

            def create(self, tenant_id: str) -> str:
                """Create entity."""
                return f"created for {tenant_id}"

            def delete(self, tenant_id: str) -> str:
                """Delete entity."""
                return f"deleted for {tenant_id}"

        repo = Repository()
        assert repo.get(tenant_id="tenant:acme") == "entity for tenant:acme"
        assert repo.create(tenant_id="tenant:acme") == "created for tenant:acme"
        assert repo.delete(tenant_id="tenant:acme") == "deleted for tenant:acme"

    def test_class_decorator_fast_break_on_missing_tenant_param(self) -> None:
        """Decorator raises SecurityDeclarationError if method lacks tenant param."""
        with pytest.raises(SecurityDeclarationError):

            @tenant_scoped("tenant_id")
            class BadRepository:
                """Repository with method missing tenant_id."""

                def get(self) -> str:
                    """Missing tenant_id parameter."""
                    return "entity"

    def test_class_decorator_self_tenant_id_skips_validation(self) -> None:
        """Decorator with self.tenant_id skips validation check."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("self.tenant_id")
        class Entity:
            """Entity with tenant_id instance attribute."""

            def __init__(self, tenant_id: str) -> None:
                """Initialize."""
                self.tenant_id = tenant_id

            def get_data(self) -> str:
                """Get data."""
                return f"data for {self.tenant_id}"

        entity = Entity(tenant_id="tenant:acme")
        assert entity.get_data() == "data for tenant:acme"

    def test_class_decorator_denies_tenant_mismatch(self) -> None:
        """Decorated class methods deny on tenant mismatch."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Tenant-scoped repository."""

            def get(self, tenant_id: str) -> str:
                """Get entity."""
                return f"entity for {tenant_id}"

        repo = Repository()
        with pytest.raises(TenancyError):
            repo.get(tenant_id="tenant:widgets")

    def test_class_decorator_skips_private_methods(self) -> None:
        """Decorator skips private methods."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Repository with private method."""

            def public_get(self, tenant_id: str) -> str:
                """Public method."""
                return self._private_get(tenant_id)

            def _private_get(self, tenant_id: str) -> str:
                """Private method without tenant_id check."""
                return f"data for {tenant_id}"

        repo = Repository()
        assert repo.public_get(tenant_id="tenant:acme") == "data for tenant:acme"
        assert repo._private_get("any") == "data for any"

    def test_class_decorator_skips_dunder_methods(self) -> None:
        """Decorator skips dunder methods."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Entity:
            """Entity with dunder method."""

            def __init__(self, tenant_id: str) -> None:
                """Initialize."""
                self.tenant_id = tenant_id

            def __str__(self) -> str:
                """String representation."""
                return f"Entity({self.tenant_id})"

            def get(self, tenant_id: str) -> str:
                """Get entity."""
                return f"entity for {tenant_id}"

        entity = Entity(tenant_id="acme")
        assert entity.get(tenant_id="tenant:acme") == "entity for tenant:acme"
        assert str(entity) == "Entity(acme)"

    def test_class_decorator_skips_properties(self) -> None:
        """Decorator skips properties."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Entity:
            """Entity with property."""

            def __init__(self, tenant_id: str) -> None:
                """Initialize."""
                self.tenant_id = tenant_id

            @property
            def name(self) -> str:
                """Get name."""
                return f"Entity-{self.tenant_id}"

            def get(self, tenant_id: str) -> str:
                """Get entity."""
                return f"entity for {tenant_id}"

        entity = Entity(tenant_id="acme")
        assert entity.get(tenant_id="tenant:acme") == "entity for tenant:acme"
        assert entity.name == "Entity-acme"

    def test_class_decorator_handles_classmethod(self) -> None:
        """Decorator handles classmethods correctly."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Factory:
            """Factory with classmethod."""

            @classmethod
            def create(cls, tenant_id: str) -> Factory:
                """Create instance."""
                return cls()

        factory = Factory.create(tenant_id="tenant:acme")
        assert isinstance(factory, Factory)

    def test_class_decorator_handles_staticmethod(self) -> None:
        """Decorator handles staticmethods correctly."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Helper:
            """Helper with staticmethod."""

            @staticmethod
            def process(tenant_id: str) -> str:
                """Process static method."""
                return f"processed {tenant_id}"

        result = Helper.process(tenant_id="tenant:acme")
        assert result == "processed tenant:acme"

    def test_class_decorator_skips_inherited_methods(self) -> None:
        """Decorator applies only to methods in class dict, not inherited."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        class BaseRepository:
            """Base repository."""

            def base_get(self, tenant_id: str) -> str:
                """Base method."""
                return f"base entity for {tenant_id}"

        @tenant_scoped("tenant_id")
        class DerivedRepository(BaseRepository):
            """Derived repository."""

            def derived_get(self, tenant_id: str) -> str:
                """Derived method."""
                return f"derived entity for {tenant_id}"

        repo = DerivedRepository()
        assert (
            repo.derived_get(tenant_id="tenant:acme")
            == "derived entity for tenant:acme"
        )
        assert repo.base_get(tenant_id="tenant:acme") == "base entity for tenant:acme"

    def test_class_decorator_method_already_decorated_skipped(self) -> None:
        """Method already decorated is not re-decorated."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Repository with mix of decorated and undecorated."""

            @tenant_scoped("other_id")
            def get_by_other(self, other_id: str) -> str:
                """Explicitly requires other_id."""
                return f"result for {other_id}"

            def get(self, tenant_id: str) -> str:
                """Requires tenant_id from class decorator."""
                return f"entity for {tenant_id}"

        repo = Repository()
        manager.set(SecurityContext(principal=principal, tenant_id="other_val"))
        assert repo.get_by_other(other_id="other_val") == "result for other_val"
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))
        assert repo.get(tenant_id="tenant:acme") == "entity for tenant:acme"

    def test_class_decorator_forwards_return_values(self) -> None:
        """Class decorator forwards return values correctly."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Repository returning different types."""

            def get_count(self, tenant_id: str) -> int:
                """Get count."""
                return 42

            def get_data(self, tenant_id: str) -> dict[str, str]:
                """Get data."""
                return {"tenant": tenant_id, "status": "ok"}

            def get_items(self, tenant_id: str) -> list[str]:
                """Get items."""
                return [tenant_id, "item1", "item2"]

        repo = Repository()
        assert repo.get_count(tenant_id="tenant:acme") == 42
        assert repo.get_data(tenant_id="tenant:acme") == {
            "tenant": "tenant:acme",
            "status": "ok",
        }
        assert repo.get_items(tenant_id="tenant:acme") == [
            "tenant:acme",
            "item1",
            "item2",
        ]

    def test_class_decorator_with_method_args(self) -> None:
        """Class decorator preserves method arguments."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Repository with methods having multiple args."""

            def update(self, tenant_id: str, entity_id: str, value: str) -> str:
                """Update entity."""
                return f"{tenant_id}:{entity_id}={value}"

            def batch_delete(
                self, tenant_id: str, ids: list[str], force: bool = False
            ) -> str:
                """Batch delete."""
                return f"deleted {len(ids)} for {tenant_id} (force={force})"

        repo = Repository()
        result = repo.update("tenant:acme", "ent1", "new_value")
        assert result == "tenant:acme:ent1=new_value"
        result = repo.batch_delete("tenant:acme", ["id1", "id2"])
        assert result == "deleted 2 for tenant:acme (force=False)"

    def test_class_decorator_missing_param_in_classmethod(self) -> None:
        """Decorator raises if classmethod lacks tenant param."""
        with pytest.raises(SecurityDeclarationError):

            @tenant_scoped("tenant_id")
            class Factory:
                """Factory with classmethod missing tenant_id."""

                @classmethod
                def create(cls) -> Factory:
                    """Create without tenant_id."""
                    return cls()

    def test_class_decorator_missing_param_in_staticmethod(self) -> None:
        """Decorator raises if staticmethod lacks tenant param."""
        with pytest.raises(SecurityDeclarationError):

            @tenant_scoped("tenant_id")
            class Helper:
                """Helper with staticmethod missing tenant_id."""

                @staticmethod
                def process() -> str:
                    """Process without tenant_id."""
                    return "result"

    def test_class_decorator_fast_break_error_includes_context(self) -> None:
        """Fast-break error includes method name and param name in context."""
        with pytest.raises(SecurityDeclarationError) as exc_info:

            @tenant_scoped("tenant_id")
            class BadRepo:
                """Repository with bad method."""

                def get(self) -> str:
                    """Missing tenant_id."""
                    return "entity"

        error = exc_info.value
        assert error.context.get("method_name") == "get"
        assert error.context.get("param_name") == "tenant_id"

    def test_class_decorator_skips_nested_classes(self) -> None:
        """Decorator skips nested classes when scanning attributes."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        manager = SecurityContextManager()
        manager.set(SecurityContext(principal=principal, tenant_id="tenant:acme"))

        @tenant_scoped("tenant_id")
        class Repository:
            """Repository with nested class."""

            class Config:
                """Nested configuration class."""

                timeout: int = 30

            def get(self, tenant_id: str) -> str:
                """Get entity."""
                return f"entity for {tenant_id}"

        repo = Repository()
        assert repo.get(tenant_id="tenant:acme") == "entity for tenant:acme"
        assert Repository.Config.timeout == 30
