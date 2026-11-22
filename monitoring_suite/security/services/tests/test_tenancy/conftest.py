"""Fixtures for tenancy tests."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)


@pytest.fixture
def principal() -> Principal:  # noqa: R004
    """
    Create a principal.

    Used by: TestTenancyGuard.
    """
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()
    return Principal(id="user:test", roles=roles, scopes=scopes)


@pytest.fixture
def context_with_tenant(principal: Principal) -> SecurityContext:  # noqa: R004
    """
    Create a context with a tenant.

    Used by: TestTenancyGuard.
    """
    return SecurityContext(principal=principal, tenant_id="tenant:acme")


@pytest.fixture
def context_without_tenant(principal: Principal) -> SecurityContext:  # noqa: R004
    """
    Create a context without a tenant.

    Used by: TestTenancyGuard.
    """
    return SecurityContext(principal=principal, tenant_id=None)
