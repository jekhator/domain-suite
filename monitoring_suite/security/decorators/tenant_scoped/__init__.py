"""Tenant-boundary enforcement decorator."""

from monitoring_suite.security.decorators.tenant_scoped.tenant_scoped_client import (
    TenantScoped,
    tenant_scoped,
)

__all__ = ["TenantScoped", "tenant_scoped"]
