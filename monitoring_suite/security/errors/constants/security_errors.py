"""
Error messages raised at the API surface (source-side; tests match against these via const.ERR_*).

Imported as const.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CODE_AUTHZ_DENIED", "CODE_SECRET_ACCESS_FAILED", "CODE_SECURITY_DECLARATION_FAILED",
    "CODE_SECURITY_ERROR", "CODE_TENANT_BOUNDARY_VIOLATION", "DOMAIN_SECURITY", "ERR_AUTHZ_PERMISSION_DENIED",
    "ERR_SECRET_ACCESS_FAILED", "ERR_SECURITY_CONSTRAINT_VIOLATED", "ERR_TENANCY_BOUNDARY_VIOLATION",
    "ERR_SECURITY_DECLARATION_FAILED", "HTTP_STATUS_FORBIDDEN", "HTTP_STATUS_INTERNAL_SERVER_ERROR"
]


"""Security constraint messages."""

ERR_SECURITY_CONSTRAINT_VIOLATED: Final[str] = "Security constraint violated."

ERR_AUTHZ_PERMISSION_DENIED: Final[str] = "Permission denied."

ERR_TENANCY_BOUNDARY_VIOLATION: Final[str] = "Tenant boundary violation."

ERR_SECRET_ACCESS_FAILED: Final[str] = "Secret access failed."


"""Decorator declaration-time validation messages."""

ERR_SECURITY_DECLARATION_FAILED: Final[str] = "Security decorator declaration failed."


"""Error class contract values: domain, codes and HTTP statuses."""

DOMAIN_SECURITY: Final[str] = "security"
CODE_SECURITY_ERROR: Final[str] = "security_error"
HTTP_STATUS_FORBIDDEN: Final[int] = 403
CODE_AUTHZ_DENIED: Final[str] = "authz_denied"
CODE_TENANT_BOUNDARY_VIOLATION: Final[str] = "tenant_boundary_violation"
CODE_SECRET_ACCESS_FAILED: Final[str] = "secret_access_failed"
HTTP_STATUS_INTERNAL_SERVER_ERROR: Final[int] = 500
CODE_SECURITY_DECLARATION_FAILED: Final[str] = "security_declaration_failed"
