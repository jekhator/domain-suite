"""Tenant-boundary enforcement against the ambient security context."""

from __future__ import annotations

from monitoring_suite.security.context.security_context.security_context_objects import SecurityContext
from monitoring_suite.security.errors.security_errors import TenancyError
from monitoring_suite.security.services.constants import tenancy as const


class TenancyGuard:
    """Verify that an operation stays inside the context's tenant boundary."""

    def check(self, ctx: SecurityContext, tenant_id: str) -> None:
        """Raise TenancyError unless the context is bound to the given tenant."""
        if ctx.tenant_id is None:
            raise TenancyError(message=const.ERR_TENANCY_NO_TENANT_BOUND, tenant_id=tenant_id)
        if ctx.tenant_id != tenant_id:
            raise TenancyError(
                message=const.ERR_TENANCY_BOUNDARY_VIOLATION, tenant_id=tenant_id, context_tenant_id=ctx.tenant_id
            )
