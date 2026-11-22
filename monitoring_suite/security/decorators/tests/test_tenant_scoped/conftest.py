"""Fixtures for tenant_scoped decorator tests."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from monitoring_suite.security.services.tenancy.tenancy_client import TenancyGuard


class StrictTenancyGuard(TenancyGuard):
    """Test tenancy guard that only allows explicitly configured tenants."""

    def __init__(self, allowed_tenants: set[str] | None = None) -> None:
        """Store allowed tenants."""
        self.allowed_tenants = allowed_tenants or set()

    def check(self, ctx: SecurityContext, tenant_id: str) -> None:
        """Check only against allowed tenants."""
        if tenant_id not in self.allowed_tenants:
            from monitoring_suite.security.errors.security_errors import TenancyError

            raise TenancyError(message="tenant not allowed", tenant_id=tenant_id)
        super().check(ctx, tenant_id)


@pytest.fixture
def principal() -> Principal:
    """
    Create a principal.

    Used by: no test class yet.
    """
    return Principal(id="user:test", roles=frozenset(), scopes=frozenset())


@pytest.fixture
def principal_with_tenant_id() -> type:
    """
    Create a class with a tenant_id attribute and decorated method.

    Used by: no test class yet.
    """

    class Entity:
        """Entity with tenant-scoped method."""

        def __init__(self, tenant_id: str) -> None:
            """Initialize with tenant_id."""
            self.tenant_id = tenant_id

    return Entity
