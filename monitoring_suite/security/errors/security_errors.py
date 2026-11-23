"""Typed security error hierarchy for authorization, tenancy, and secret failures."""

from __future__ import annotations

from monitoring_suite.errors import DomainError
from monitoring_suite.security.errors.constants import security_errors as const


class SecurityError(DomainError):
    """Base error for all security-domain failures."""

    domain = const.DOMAIN_SECURITY
    code = const.CODE_SECURITY_ERROR
    http_status = const.HTTP_STATUS_FORBIDDEN
    retryable = False
    default_message = const.ERR_SECURITY_CONSTRAINT_VIOLATED


class AuthzError(SecurityError):
    """Permission denied by authorization policy."""

    code = const.CODE_AUTHZ_DENIED
    default_message = const.ERR_AUTHZ_PERMISSION_DENIED


class TenancyError(SecurityError):
    """Operation crossed or lacked a tenant boundary."""

    code = const.CODE_TENANT_BOUNDARY_VIOLATION
    default_message = const.ERR_TENANCY_BOUNDARY_VIOLATION


class SecretError(SecurityError):
    """Secret resolution or access failure."""

    code = const.CODE_SECRET_ACCESS_FAILED
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    default_message = const.ERR_SECRET_ACCESS_FAILED


class SecurityDeclarationError(SecurityError):
    """Decorator declaration-time validation failure."""

    code = const.CODE_SECURITY_DECLARATION_FAILED
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_SECURITY_DECLARATION_FAILED
