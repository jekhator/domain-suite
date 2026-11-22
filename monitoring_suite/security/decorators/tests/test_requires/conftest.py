"""Fixtures for requires decorator tests."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from monitoring_suite.security.services.authz.authz_client import Authorizer
from monitoring_suite.security.services.authz.authz_objects import (
    Permission,
    PolicyDecision,
)


class AlwaysAllowAuthorizer(Authorizer):
    """Test authorizer that always allows."""

    def check(self, ctx: SecurityContext, permission: Permission) -> PolicyDecision:
        """Always allow access."""
        return PolicyDecision(allowed=True)


class AlwaysDenyAuthorizer(Authorizer):
    """Test authorizer that always denies."""

    def check(self, ctx: SecurityContext, permission: Permission) -> PolicyDecision:
        """Always deny access."""
        return PolicyDecision(allowed=False, reason="always denied")


@pytest.fixture
def principal_with_read_scope() -> Principal:
    """Create a principal with read scope."""
    return Principal(id="user:reader", roles=frozenset(), scopes=frozenset(["read"]))


@pytest.fixture
def always_allow_authorizer() -> Authorizer:
    """Create an authorizer that always allows."""
    return AlwaysAllowAuthorizer()


@pytest.fixture
def always_deny_authorizer() -> Authorizer:
    """Create an authorizer that always denies."""
    return AlwaysDenyAuthorizer()
