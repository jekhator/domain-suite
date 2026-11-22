"""Typed security error hierarchy for authorization, tenancy, and secret failures."""

from __future__ import annotations

from monitoring_suite.errors import DomainError
from monitoring_suite.security.errors.constants import security_errors as const


class SecurityError(DomainError):
    """Base error for all security-domain failures."""

    domain = "security"
    code = "security_error"
    http_status = 403
    retryable = False
    default_message = const.ERR_SECURITY_CONSTRAINT_VIOLATED


class AuthzError(SecurityError):
    """Permission denied by authorization policy."""

    code = "authz_denied"
    default_message = const.ERR_AUTHZ_PERMISSION_DENIED


class TenancyError(SecurityError):
    """Operation crossed or lacked a tenant boundary."""

    code = "tenant_boundary_violation"
    default_message = const.ERR_TENANCY_BOUNDARY_VIOLATION


class SecretError(SecurityError):
    """Secret resolution or access failure."""

    code = "secret_access_failed"
    http_status = 500
    default_message = const.ERR_SECRET_ACCESS_FAILED


class SecurityDeclarationError(SecurityError):
    """Decorator declaration-time validation failure."""

    code = "security_declaration_failed"
    http_status = 500
    retryable = False
    default_message = const.ERR_SECURITY_DECLARATION_FAILED
