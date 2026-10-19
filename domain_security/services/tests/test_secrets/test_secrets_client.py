"""Tests for secret reference resolution."""

from __future__ import annotations

import pytest

from domain_security.errors.security_errors import SecretError
from domain_security.services.constants import secrets as const
from domain_security.services.secrets.secrets_client import SecretRef
from domain_security.services.secrets.secrets_objects import SecretValue


class TestSecretRef:
    """SecretRef lazy resolution through pluggable backend."""

    def test_init_stores_name(self) -> None:
        """SecretRef stores the secret name."""
        ref = SecretRef(name="db_password")
        assert ref.name == "db_password"

    def test_resolve_with_backend_returns_secret_value(self, fake_backend) -> None:
        """resolve returns a SecretValue when backend fetch succeeds."""
        ref = SecretRef(name="db_password")
        result = ref.resolve(backend=fake_backend)
        assert isinstance(result, SecretValue)
        assert result.get() == "super_secret_123"

    def test_resolve_no_backend_raises_secret_error(self) -> None:
        """resolve raises SecretError when no backend provided."""
        ref = SecretRef(name="db_password")
        with pytest.raises(SecretError) as exc_info:
            ref.resolve(backend=None)
        assert exc_info.value.code == "secret_access_failed"
        assert exc_info.value.context["secret_name"] == "db_password"

    def test_resolve_no_backend_error_not_double_wrapped(self) -> None:
        """resolve with no backend raises SecretError directly, not wrapped."""
        ref = SecretRef(name="db_password")
        with pytest.raises(SecretError) as exc_info:
            ref.resolve(backend=None)
        assert exc_info.value.__cause__ is None

    def test_resolve_backend_failure_wrapped_in_secret_error(
        self, failing_backend
    ) -> None:
        """resolve wraps backend exceptions in SecretError with __cause__."""
        ref = SecretRef(name="missing_secret")
        with pytest.raises(SecretError) as exc_info:
            ref.resolve(backend=failing_backend)
        assert exc_info.value.code == "secret_access_failed"
        assert isinstance(exc_info.value.__cause__, KeyError)

    def test_resolve_multiple_secrets(self, fake_backend) -> None:
        """resolve works for multiple different secrets."""
        ref1 = SecretRef(name="db_password")
        ref2 = SecretRef(name="api_key")
        secret1 = ref1.resolve(backend=fake_backend)
        secret2 = ref2.resolve(backend=fake_backend)
        assert secret1.get() == "super_secret_123"
        assert secret2.get() == "key_abc_xyz"

    def test_resolve_returns_masked_repr(self, fake_backend) -> None:
        """resolve returns SecretValue with masked repr."""
        ref = SecretRef(name="db_password")
        secret = ref.resolve(backend=fake_backend)
        assert repr(secret) == const.SECRET_VALUE_MASKED_REPR
        assert "super_secret_123" not in repr(secret)

    def test_resolve_preserves_plaintext_via_get(self, fake_backend) -> None:
        """resolve allows get to retrieve plaintext despite masked repr."""
        ref = SecretRef(name="db_password")
        secret = ref.resolve(backend=fake_backend)
        plaintext = secret.get()
        assert plaintext == "super_secret_123"
        assert plaintext not in repr(secret)

    def test_resolve_backend_exception_cause_preserved(self, failing_backend) -> None:
        """resolve preserves the original exception as __cause__."""
        ref = SecretRef(name="nonexistent")
        with pytest.raises(SecretError) as exc_info:
            ref.resolve(backend=failing_backend)
        cause = exc_info.value.__cause__
        assert isinstance(cause, KeyError)
        assert "nonexistent" in str(cause)

    def test_resolve_with_punctuated_secret_names(self, fake_backend) -> None:
        """resolve passes secret names containing slashes, dashes and dots to the backend unchanged."""
        ref = SecretRef(name="app/db-password.v2")
        secret = ref.resolve(backend=fake_backend)
        assert secret.get() == "punctuated_456"

    def test_resolve_error_message_includes_secret_name(self) -> None:
        """resolve error includes the requested secret name."""
        ref = SecretRef(name="missing")
        with pytest.raises(SecretError) as exc_info:
            ref.resolve(backend=None)
        assert exc_info.value.context.get("secret_name") == "missing"
