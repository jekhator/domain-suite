"""Tests for tenant boundary enforcement."""

from __future__ import annotations

import pytest

from domain_security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from domain_security.errors.security_errors import TenancyError
from domain_security.services.constants import tenancy as const
from domain_security.services.tenancy.tenancy_client import TenancyGuard


class TestTenancyGuard:
    """TenancyGuard tenant boundary enforcement."""

    def test_check_passes_matching_tenant(
        self, context_with_tenant: SecurityContext
    ) -> None:
        """check does not raise when context tenant matches requested tenant."""
        guard = TenancyGuard()
        guard.check(context_with_tenant, "tenant:acme")

    def test_check_raises_no_tenant_bound(
        self, context_without_tenant: SecurityContext
    ) -> None:
        """check raises TenancyError when context has no tenant."""
        guard = TenancyGuard()
        with pytest.raises(TenancyError) as exc_info:
            guard.check(context_without_tenant, "tenant:acme")
        assert exc_info.value.code == "tenant_boundary_violation"
        assert exc_info.value.message == const.ERR_TENANCY_NO_TENANT_BOUND

    def test_check_raises_tenant_mismatch(
        self, context_with_tenant: SecurityContext
    ) -> None:
        """check raises TenancyError when context tenant differs from requested."""
        guard = TenancyGuard()
        with pytest.raises(TenancyError) as exc_info:
            guard.check(context_with_tenant, "tenant:widgets")
        assert exc_info.value.code == "tenant_boundary_violation"
        assert exc_info.value.message == const.ERR_TENANCY_BOUNDARY_VIOLATION

    def test_check_includes_tenant_ids_in_context(
        self, context_with_tenant: SecurityContext
    ) -> None:
        """check includes both tenant IDs in error context."""
        guard = TenancyGuard()
        with pytest.raises(TenancyError) as exc_info:
            guard.check(context_with_tenant, "tenant:widgets")
        assert exc_info.value.context["tenant_id"] == "tenant:widgets"
        assert exc_info.value.context["context_tenant_id"] == "tenant:acme"

    def test_check_no_tenant_bound_includes_requested_tenant(
        self, context_without_tenant: SecurityContext
    ) -> None:
        """check includes requested tenant_id when context has none."""
        guard = TenancyGuard()
        with pytest.raises(TenancyError) as exc_info:
            guard.check(context_without_tenant, "tenant:requested")
        assert exc_info.value.context["tenant_id"] == "tenant:requested"

    def test_check_accepts_various_tenant_formats(self, principal: Principal) -> None:
        """check accepts various tenant identifier formats."""
        guard = TenancyGuard()
        tenant_ids = ["tenant:123", "org:abc", "workspace:xyz", "simple"]
        for tenant_id in tenant_ids:
            ctx = SecurityContext(principal=principal, tenant_id=tenant_id)
            guard.check(ctx, tenant_id)

    def test_check_case_sensitive_tenant_comparison(self, principal: Principal) -> None:
        """check tenant comparison is case-sensitive."""
        guard = TenancyGuard()
        ctx = SecurityContext(principal=principal, tenant_id="TENANT:ACME")
        with pytest.raises(TenancyError):
            guard.check(ctx, "tenant:acme")

    def test_check_with_anonymous_principal(self) -> None:
        """check works with anonymous principal."""
        guard = TenancyGuard()
        ctx = SecurityContext(principal=None, tenant_id="tenant:acme")
        guard.check(ctx, "tenant:acme")

    def test_check_colon_delimited_tenant_ids(self, principal: Principal) -> None:
        """check accepts colon-delimited multi-part tenant identifiers."""
        guard = TenancyGuard()
        complex_tenant = "tenant:multi:part:identifier"
        ctx = SecurityContext(principal=principal, tenant_id=complex_tenant)
        guard.check(ctx, complex_tenant)
