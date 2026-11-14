"""Tests for security context management."""

from __future__ import annotations

from contextvars import Token

import pytest

from domain_security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from domain_security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)


class TestSecurityContextManager:
    """SecurityContextManager ambient context operations."""

    def test_get_none_when_unset(self) -> None:
        """get returns None when no context is set."""
        manager = SecurityContextManager()
        assert manager.get() is None

    def test_set_and_get(self, security_context: SecurityContext) -> None:
        """set stores context and get retrieves it."""
        manager = SecurityContextManager()
        manager.set(security_context)
        assert manager.get() == security_context

    def test_set_returns_token(self, security_context: SecurityContext) -> None:
        """set returns a token that can be used to reset."""
        manager = SecurityContextManager()
        token = manager.set(security_context)
        assert isinstance(token, Token)

    def test_clear_resets_to_previous(
        self, security_context: SecurityContext, anonymous_context: SecurityContext
    ) -> None:
        """clear resets context to state before matching set call."""
        manager = SecurityContextManager()
        token1 = manager.set(anonymous_context)
        manager.set(security_context)
        assert manager.get() == security_context
        manager.clear(token1)
        assert manager.get() is None

    def test_clear_restores_previous_context(
        self, security_context: SecurityContext, anonymous_context: SecurityContext
    ) -> None:
        """clear restores the prior context when clearing a later set."""
        manager = SecurityContextManager()
        manager.set(anonymous_context)
        token2 = manager.set(security_context)
        assert manager.get() == security_context
        manager.clear(token2)
        assert manager.get() == anonymous_context

    def test_bind_context_manager_sets_context(
        self, security_context: SecurityContext
    ) -> None:
        """bind sets the context for the with-block."""
        manager = SecurityContextManager()
        with manager.bind(
            principal=security_context.principal, tenant_id=security_context.tenant_id
        ):
            assert manager.get() == security_context

    def test_bind_restores_prior_after_exit(
        self, security_context: SecurityContext, anonymous_context: SecurityContext
    ) -> None:
        """bind restores the prior context after the with-block exits."""
        manager = SecurityContextManager()
        manager.set(anonymous_context)
        with manager.bind(
            principal=security_context.principal, tenant_id=security_context.tenant_id
        ):
            assert manager.get() == security_context
        assert manager.get() == anonymous_context

    def test_bind_restores_after_exception(
        self, security_context: SecurityContext, anonymous_context: SecurityContext
    ) -> None:
        """bind restores prior context even when exception raised inside with-block."""
        manager = SecurityContextManager()
        manager.set(anonymous_context)
        with pytest.raises(ValueError):
            with manager.bind(
                principal=security_context.principal,
                tenant_id=security_context.tenant_id,
            ):
                assert manager.get() == security_context
                raise ValueError("test error")
        assert manager.get() == anonymous_context

    def test_bind_with_none_principal(self) -> None:
        """bind accepts None principal for anonymous binding."""
        manager = SecurityContextManager()
        with manager.bind(principal=None, tenant_id="tenant:test"):
            ctx = manager.get()
            assert ctx is not None
            assert ctx.principal is None
            assert ctx.tenant_id == "tenant:test"

    def test_bind_with_none_tenant_id(self, principal: Principal) -> None:
        """bind accepts None tenant_id for unscoped binding."""
        manager = SecurityContextManager()
        with manager.bind(principal=principal, tenant_id=None):
            ctx = manager.get()
            assert ctx is not None
            assert ctx.principal == principal
            assert ctx.tenant_id is None

    def test_nested_bind_operations(
        self, security_context: SecurityContext, anonymous_context: SecurityContext
    ) -> None:
        """nested bind operations maintain stack discipline."""
        manager = SecurityContextManager()
        with manager.bind(
            principal=anonymous_context.principal,
            tenant_id=anonymous_context.tenant_id,
        ):
            assert manager.get() == anonymous_context
            with manager.bind(
                principal=security_context.principal,
                tenant_id=security_context.tenant_id,
            ):
                assert manager.get() == security_context
            assert manager.get() == anonymous_context

    def test_fresh_bind_semantics_replaces_context(
        self, security_context: SecurityContext, principal: Principal
    ) -> None:
        """bind replaces context entirely, not merging with existing."""
        manager = SecurityContextManager()
        manager.set(security_context)
        other_principal = Principal(
            id="user:other", roles=frozenset(), scopes=frozenset()
        )
        with manager.bind(principal=other_principal, tenant_id="tenant:other"):
            ctx = manager.get()
            assert ctx is not None
            assert ctx.principal == other_principal
            assert ctx.tenant_id == "tenant:other"
            assert ctx != security_context

    def test_bind_returns_context_manager(
        self, security_context: SecurityContext
    ) -> None:
        """bind returns an AbstractContextManager."""
        manager = SecurityContextManager()
        cm = manager.bind(
            principal=security_context.principal,
            tenant_id=security_context.tenant_id,
        )
        assert hasattr(cm, "__enter__")
        assert hasattr(cm, "__exit__")
