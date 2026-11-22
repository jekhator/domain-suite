"""Scope-based authorization policy evaluation."""

from __future__ import annotations

from monitoring_suite.security.context.security_context.security_context_objects import (
    SecurityContext,
)
from monitoring_suite.security.errors.security_errors import AuthzError
from monitoring_suite.security.services.authz import authz_objects as objs
from monitoring_suite.security.services.constants import authz as const


class Authorizer:
    """Scope-based policy evaluation; subclasses override check for richer policy sources."""

    def check(
        self,
        ctx: SecurityContext,
        permission: objs.Permission,
    ) -> objs.PolicyDecision:
        """Evaluate the permission against the context and return the decision."""
        if ctx.principal is None:
            return objs.PolicyDecision(
                allowed=False, reason=const.ERR_AUTHZ_NO_PRINCIPAL
            )
        if permission.value not in ctx.principal.scopes:
            reason = const.ERR_AUTHZ_MISSING_SCOPE.format(scope=permission.value)
            return objs.PolicyDecision(
                allowed=False,
                reason=reason,
            )
        return objs.PolicyDecision(allowed=True)

    def require(self, ctx: SecurityContext, permission: objs.Permission) -> None:
        """Enforce the permission, raising AuthzError when denied."""
        decision = self.check(ctx, permission)
        if not decision.allowed:
            raise AuthzError(
                message=decision.reason,
                permission=permission.value,
            )
