"""Fixtures for security context tests."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import Principal, SecurityContext


@pytest.fixture
def principal() -> Principal:
    """
    Create a principal with default roles and scopes.

    Used by: TestSecurityContextManager.
    """
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()
    return Principal(id="user:test", roles=roles, scopes=scopes)


@pytest.fixture
def principal_with_scopes() -> Principal:
    """
    Create a principal with scopes.

    Used by: no test class yet.
    """
    roles = frozenset(["admin"])
    scopes = frozenset(["read", "write", "delete"])
    return Principal(id="user:admin", roles=roles, scopes=scopes)


@pytest.fixture
def security_context() -> SecurityContext:
    """
    Create a security context with a principal and tenant.

    Used by: TestSecurityContextManager.
    """
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()
    principal = Principal(id="user:test", roles=roles, scopes=scopes)
    return SecurityContext(principal=principal, tenant_id="tenant:acme")


@pytest.fixture
def anonymous_context() -> SecurityContext:
    """
    Create an anonymous security context.

    Used by: TestSecurityContextManager.
    """
    return SecurityContext(principal=None, tenant_id=None)
