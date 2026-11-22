"""Fixtures for authorization tests."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from monitoring_suite.security.services.authz.authz_objects import Permission


@pytest.fixture
def permission() -> Permission:  # noqa: R004
    """
    Create a permission.

    Used by: TestAuthorizer.
    """
    return Permission(value="read")


@pytest.fixture
def write_permission() -> Permission:  # noqa: R004
    """
    Create a write permission.

    Used by: TestAuthorizer.
    """
    return Permission(value="write")


@pytest.fixture
def delete_permission() -> Permission:  # noqa: R004
    """
    Create a delete permission.

    Used by: no test class yet.
    """
    return Permission(value="delete")


@pytest.fixture
def principal_with_read_scope() -> Principal:  # noqa: R004
    """
    Create a principal with read scope.

    Used by: TestAuthorizer.
    """
    roles: frozenset[str] = frozenset()
    scopes = frozenset(["read"])
    return Principal(id="user:reader", roles=roles, scopes=scopes)


@pytest.fixture
def principal_with_multiple_scopes() -> Principal:  # noqa: R004
    """
    Create a principal with multiple scopes.

    Used by: TestAuthorizer.
    """
    roles = frozenset(["admin"])
    scopes = frozenset(["read", "write", "delete"])
    return Principal(
        id="user:admin",
        roles=roles,
        scopes=scopes,
    )


@pytest.fixture
def context_with_principal(  # noqa: R004
    principal_with_read_scope: Principal,
) -> SecurityContext:
    """
    Create a security context with a principal.

    Used by: no test class yet.
    """
    return SecurityContext(principal=principal_with_read_scope, tenant_id="tenant:test")
