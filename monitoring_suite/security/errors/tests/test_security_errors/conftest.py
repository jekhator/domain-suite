"""Fixtures for security errors tests."""

from __future__ import annotations

import pytest

from monitoring_suite.security.errors.security_errors import (
    AuthzError,
    SecretError,
    SecurityError,
    TenancyError,
)


@pytest.fixture
def security_error() -> SecurityError:
    """Create a SecurityError."""
    return SecurityError(message="Security constraint violated")


@pytest.fixture
def authz_error() -> AuthzError:
    """Create an AuthzError."""
    return AuthzError(message="Permission denied", permission="read")


@pytest.fixture
def tenancy_error() -> TenancyError:
    """Create a TenancyError."""
    return TenancyError(
        message="Tenant boundary violation",
        tenant_id="tenant:test",
    )


@pytest.fixture
def secret_error() -> SecretError:
    """Create a SecretError."""
    return SecretError(message="Secret access failed", secret_name="db_password")
