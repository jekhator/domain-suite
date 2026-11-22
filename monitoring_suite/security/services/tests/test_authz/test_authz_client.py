"""Tests for authorization policy evaluation."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from monitoring_suite.security.errors.security_errors import AuthzError
from monitoring_suite.security.services.authz.authz_client import Authorizer
from monitoring_suite.security.services.authz.authz_objects import (
    Permission,
    PolicyDecision,
)
from monitoring_suite.security.services.constants import authz as const


class TestAuthorizer:
    """Authorizer scope-based policy evaluation."""

    def test_check_denies_no_principal(self, permission: Permission) -> None:
        """check denies access when context has no principal."""
        authorizer = Authorizer()
        context = SecurityContext(principal=None, tenant_id="tenant:test")
        decision = authorizer.check(context, permission)
        assert decision.allowed is False
        assert decision.reason == const.ERR_AUTHZ_NO_PRINCIPAL

    def test_check_denies_missing_scope(
        self, principal_with_read_scope: Principal, write_permission: Permission
    ) -> None:
        """check denies access when principal lacks required scope."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        decision = authorizer.check(context, write_permission)
        assert decision.allowed is False
        assert decision.reason == const.ERR_AUTHZ_MISSING_SCOPE.format(
            scope=write_permission.value
        )

    def test_check_allows_with_scope(
        self, principal_with_read_scope: Principal, permission: Permission
    ) -> None:
        """check allows access when principal has required scope."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        decision = authorizer.check(context, permission)
        assert decision.allowed is True
        assert decision.reason is None

    def test_check_allows_with_multiple_scopes(
        self,
        principal_with_multiple_scopes: Principal,
        write_permission: Permission,
    ) -> None:
        """check allows access when principal has one of multiple scopes."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_multiple_scopes, tenant_id="tenant:test"
        )
        decision = authorizer.check(context, write_permission)
        assert decision.allowed is True

    def test_require_raises_authz_error_when_denied(
        self, principal_with_read_scope: Principal, write_permission: Permission
    ) -> None:
        """require raises AuthzError when permission is denied."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        with pytest.raises(AuthzError) as exc_info:
            authorizer.require(context, write_permission)
        assert exc_info.value.code == "authz_denied"
        assert exc_info.value.context["permission"] == "write"

    def test_require_uses_decision_reason_as_message(
        self, principal_with_read_scope: Principal, write_permission: Permission
    ) -> None:
        """require uses the decision reason as error message."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        with pytest.raises(AuthzError) as exc_info:
            authorizer.require(context, write_permission)
        assert exc_info.value.message == const.ERR_AUTHZ_MISSING_SCOPE.format(
            scope=write_permission.value
        )

    def test_require_does_not_raise_when_allowed(
        self, principal_with_read_scope: Principal, permission: Permission
    ) -> None:
        """require does not raise when permission is allowed."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        authorizer.require(context, permission)

    def test_check_returns_policy_decision(
        self, principal_with_read_scope: Principal, permission: Permission
    ) -> None:
        """check returns a PolicyDecision object."""
        authorizer = Authorizer()
        context = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        decision = authorizer.check(context, permission)
        assert isinstance(decision, PolicyDecision)

    def test_require_raises_with_no_principal_message(
        self, permission: Permission
    ) -> None:
        """require raises with no principal reason when principal is None."""
        authorizer = Authorizer()
        context = SecurityContext(principal=None, tenant_id="tenant:test")
        with pytest.raises(AuthzError) as exc_info:
            authorizer.require(context, permission)
        assert exc_info.value.message == const.ERR_AUTHZ_NO_PRINCIPAL

    def test_authorizer_subclass_can_override_check(
        self, principal_with_read_scope: Principal, permission: Permission
    ) -> None:
        """Authorizer subclasses can override check for custom policy."""

        class CustomAuthorizer(Authorizer):
            def check(
                self, ctx: SecurityContext, permission: Permission
            ) -> PolicyDecision:
                return PolicyDecision(allowed=True)

        authorizer = CustomAuthorizer()
        ctx = SecurityContext(
            principal=principal_with_read_scope, tenant_id="tenant:test"
        )
        decision = authorizer.check(ctx, permission)
        assert decision.allowed is True
