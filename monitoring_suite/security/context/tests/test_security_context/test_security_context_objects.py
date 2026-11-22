"""Tests for security context value objects."""

from __future__ import annotations

import dataclasses

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)


class TestPrincipal:
    """Principal value object behavior."""

    def test_principal_frozen(self) -> None:
        """Principal is immutable after construction."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        with pytest.raises(dataclasses.FrozenInstanceError):
            principal.id = "user:other"  # type: ignore[misc]

    def test_principal_default_roles(self) -> None:
        """Principal roles default to empty frozenset."""
        principal = Principal(id="user:test")
        assert principal.roles == frozenset()

    def test_principal_default_scopes(self) -> None:
        """Principal scopes default to empty frozenset."""
        principal = Principal(id="user:test")
        assert principal.scopes == frozenset()

    def test_principal_with_roles_and_scopes(self) -> None:
        """Principal stores roles and scopes correctly."""
        roles = frozenset(["admin", "operator"])
        scopes = frozenset(["read", "write", "delete"])
        principal = Principal(id="user:admin", roles=roles, scopes=scopes)
        assert principal.id == "user:admin"
        assert principal.roles == roles
        assert principal.scopes == scopes

    def test_principal_equality(self) -> None:
        """Principals with same data are equal."""
        p1 = Principal(
            id="user:test",
            roles=frozenset(["admin"]),
            scopes=frozenset(["read"]),
        )
        p2 = Principal(
            id="user:test",
            roles=frozenset(["admin"]),
            scopes=frozenset(["read"]),
        )
        assert p1 == p2

    def test_principal_inequality(self) -> None:
        """Principals with different data are not equal."""
        p1 = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        p2 = Principal(id="user:other", roles=frozenset(), scopes=frozenset())
        assert p1 != p2


class TestSecurityContext:
    """SecurityContext value object behavior."""

    def test_security_context_frozen(self) -> None:
        """SecurityContext is immutable after construction."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        context = SecurityContext(principal=principal, tenant_id="tenant:test")
        with pytest.raises(dataclasses.FrozenInstanceError):
            context.tenant_id = "tenant:other"  # type: ignore[misc]

    def test_security_context_with_principal_and_tenant(self) -> None:
        """SecurityContext stores principal and tenant_id correctly."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        context = SecurityContext(principal=principal, tenant_id="tenant:acme")
        assert context.principal == principal
        assert context.tenant_id == "tenant:acme"

    def test_security_context_principal_none(self) -> None:
        """SecurityContext accepts None principal for anonymous access."""
        context = SecurityContext(principal=None, tenant_id="tenant:test")
        assert context.principal is None
        assert context.tenant_id == "tenant:test"

    def test_security_context_tenant_id_none(self) -> None:
        """SecurityContext accepts None tenant_id for unscoped access."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        context = SecurityContext(principal=principal, tenant_id=None)
        assert context.principal == principal
        assert context.tenant_id is None

    def test_security_context_both_none(self) -> None:
        """SecurityContext can have both principal and tenant_id as None."""
        context = SecurityContext(principal=None, tenant_id=None)
        assert context.principal is None
        assert context.tenant_id is None

    def test_security_context_equality(self) -> None:
        """SecurityContexts with same data are equal."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        ctx1 = SecurityContext(principal=principal, tenant_id="tenant:acme")
        ctx2 = SecurityContext(principal=principal, tenant_id="tenant:acme")
        assert ctx1 == ctx2

    def test_security_context_inequality_principal(self) -> None:
        """SecurityContexts with different principals are not equal."""
        p1 = Principal(id="user:alice", roles=frozenset(), scopes=frozenset())
        p2 = Principal(id="user:bob", roles=frozenset(), scopes=frozenset())
        ctx1 = SecurityContext(principal=p1, tenant_id="tenant:acme")
        ctx2 = SecurityContext(principal=p2, tenant_id="tenant:acme")
        assert ctx1 != ctx2

    def test_security_context_inequality_tenant(self) -> None:
        """SecurityContexts with different tenant_ids are not equal."""
        principal = Principal(id="user:test", roles=frozenset(), scopes=frozenset())
        ctx1 = SecurityContext(principal=principal, tenant_id="tenant:acme")
        ctx2 = SecurityContext(principal=principal, tenant_id="tenant:widgets")
        assert ctx1 != ctx2
