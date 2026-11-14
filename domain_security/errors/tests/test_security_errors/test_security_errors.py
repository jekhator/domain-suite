"""Tests for typed security error hierarchy."""

from __future__ import annotations

from domain_errors import DomainError
from domain_security.errors.constants import security_errors as const
from domain_security.errors.security_errors import (
    AuthzError,
    SecretError,
    SecurityDeclarationError,
    SecurityError,
    TenancyError,
)


class TestSecurityError:
    """SecurityError base class behavior."""

    def test_security_error_is_domain_error(self) -> None:
        """SecurityError inherits from DomainError."""
        assert issubclass(SecurityError, DomainError)

    def test_security_error_domain(self) -> None:
        """SecurityError has domain 'security'."""
        error = SecurityError(message="test")
        assert error.domain == "security"

    def test_security_error_code(self) -> None:
        """SecurityError has code 'security_error'."""
        error = SecurityError(message="test")
        assert error.code == "security_error"

    def test_security_error_http_status(self) -> None:
        """SecurityError has http_status 403."""
        error = SecurityError(message="test")
        assert error.http_status == 403

    def test_security_error_retryable(self) -> None:
        """SecurityError is not retryable."""
        error = SecurityError(message="test")
        assert error.retryable is False

    def test_security_error_default_message(self) -> None:
        """SecurityError has default message."""
        error = SecurityError()
        assert error.message == const.ERR_SECURITY_CONSTRAINT_VIOLATED

    def test_security_error_custom_message(self) -> None:
        """SecurityError accepts custom message."""
        error = SecurityError(message="Custom message")
        assert error.message == "Custom message"

    def test_security_error_context_storage(self) -> None:
        """SecurityError stores context dict."""
        error = SecurityError(message="test", resource_id="123", action="read")
        assert error.context["resource_id"] == "123"
        assert error.context["action"] == "read"


class TestAuthzError:
    """AuthzError authorization failure."""

    def test_authz_error_is_security_error(self) -> None:
        """AuthzError inherits from SecurityError."""
        assert issubclass(AuthzError, SecurityError)

    def test_authz_error_code(self) -> None:
        """AuthzError has code 'authz_denied'."""
        error = AuthzError(message="test")
        assert error.code == "authz_denied"

    def test_authz_error_domain(self) -> None:
        """AuthzError inherits domain from SecurityError."""
        error = AuthzError(message="test")
        assert error.domain == "security"

    def test_authz_error_http_status(self) -> None:
        """AuthzError inherits http_status 403."""
        error = AuthzError(message="test")
        assert error.http_status == 403

    def test_authz_error_retryable(self) -> None:
        """AuthzError inherits retryable false."""
        error = AuthzError(message="test")
        assert error.retryable is False

    def test_authz_error_default_message(self) -> None:
        """AuthzError has default message."""
        error = AuthzError()
        assert error.message == const.ERR_AUTHZ_PERMISSION_DENIED

    def test_authz_error_with_permission_context(self) -> None:
        """AuthzError can store permission in context."""
        error = AuthzError(message="Permission denied", permission="admin")
        assert error.context["permission"] == "admin"


class TestTenancyError:
    """TenancyError tenant boundary violation."""

    def test_tenancy_error_is_security_error(self) -> None:
        """TenancyError inherits from SecurityError."""
        assert issubclass(TenancyError, SecurityError)

    def test_tenancy_error_code(self) -> None:
        """TenancyError has code 'tenant_boundary_violation'."""
        error = TenancyError(message="test")
        assert error.code == "tenant_boundary_violation"

    def test_tenancy_error_domain(self) -> None:
        """TenancyError inherits domain from SecurityError."""
        error = TenancyError(message="test")
        assert error.domain == "security"

    def test_tenancy_error_http_status(self) -> None:
        """TenancyError inherits http_status 403."""
        error = TenancyError(message="test")
        assert error.http_status == 403

    def test_tenancy_error_retryable(self) -> None:
        """TenancyError inherits retryable false."""
        error = TenancyError(message="test")
        assert error.retryable is False

    def test_tenancy_error_default_message(self) -> None:
        """TenancyError has default message."""
        error = TenancyError()
        assert error.message == const.ERR_TENANCY_BOUNDARY_VIOLATION

    def test_tenancy_error_with_tenant_context(self) -> None:
        """TenancyError can store tenant IDs in context."""
        error = TenancyError(
            message="test", tenant_id="tenant:acme", context_tenant_id="tenant:widgets"
        )
        assert error.context["tenant_id"] == "tenant:acme"
        assert error.context["context_tenant_id"] == "tenant:widgets"


class TestSecretError:
    """SecretError secret access failure."""

    def test_secret_error_is_security_error(self) -> None:
        """SecretError inherits from SecurityError."""
        assert issubclass(SecretError, SecurityError)

    def test_secret_error_code(self) -> None:
        """SecretError has code 'secret_access_failed'."""
        error = SecretError(message="test")
        assert error.code == "secret_access_failed"

    def test_secret_error_domain(self) -> None:
        """SecretError inherits domain from SecurityError."""
        error = SecretError(message="test")
        assert error.domain == "security"

    def test_secret_error_http_status(self) -> None:
        """SecretError has http_status 500 (not 403)."""
        error = SecretError(message="test")
        assert error.http_status == 500

    def test_secret_error_retryable(self) -> None:
        """SecretError inherits retryable false."""
        error = SecretError(message="test")
        assert error.retryable is False

    def test_secret_error_default_message(self) -> None:
        """SecretError has default message."""
        error = SecretError()
        assert error.message == const.ERR_SECRET_ACCESS_FAILED

    def test_secret_error_with_secret_name_context(self) -> None:
        """SecretError can store secret name in context."""
        error = SecretError(message="test", secret_name="db_password")
        assert error.context["secret_name"] == "db_password"


class TestSecurityDeclarationError:
    """SecurityDeclarationError decorator declaration failure."""

    def test_declaration_error_is_security_error(self) -> None:
        """SecurityDeclarationError inherits from SecurityError."""
        assert issubclass(SecurityDeclarationError, SecurityError)

    def test_declaration_error_code(self) -> None:
        """SecurityDeclarationError has code 'security_declaration_failed'."""
        error = SecurityDeclarationError(message="test")
        assert error.code == "security_declaration_failed"

    def test_declaration_error_http_status(self) -> None:
        """SecurityDeclarationError has http_status 500 (not 403)."""
        error = SecurityDeclarationError(message="test")
        assert error.http_status == 500

    def test_declaration_error_default_message(self) -> None:
        """SecurityDeclarationError has default message."""
        error = SecurityDeclarationError()
        assert error.message == const.ERR_SECURITY_DECLARATION_FAILED


class TestErrorHierarchy:
    """Error class hierarchy validation."""

    def test_all_security_errors_are_domain_errors(self) -> None:
        """All security errors inherit from DomainError."""
        errors = [SecurityError, AuthzError, TenancyError, SecretError]
        for error_class in errors:
            assert issubclass(error_class, DomainError)

    def test_specialized_errors_inherit_from_security_error(self) -> None:
        """Specialized errors inherit from SecurityError."""
        errors = [AuthzError, TenancyError, SecretError]
        for error_class in errors:
            assert issubclass(error_class, SecurityError)

    def test_error_codes_are_unique(self) -> None:
        """Each error class has a unique code."""
        codes = {
            SecurityError().code,
            AuthzError().code,
            TenancyError().code,
            SecretError().code,
        }
        assert len(codes) == 4

    def test_error_domain_consistency(self) -> None:
        """All errors have domain 'security'."""
        errors = [
            SecurityError(),
            AuthzError(),
            TenancyError(),
            SecretError(),
        ]
        for error in errors:
            assert error.domain == "security"

    def test_error_instantiation_with_context(self) -> None:
        """All errors accept message and context kwargs."""
        error1 = SecurityError(message="msg", key1="val1")
        error2 = AuthzError(message="msg", key2="val2")
        error3 = TenancyError(message="msg", key3="val3")
        error4 = SecretError(message="msg", key4="val4")
        assert error1.context["key1"] == "val1"
        assert error2.context["key2"] == "val2"
        assert error3.context["key3"] == "val3"
        assert error4.context["key4"] == "val4"
