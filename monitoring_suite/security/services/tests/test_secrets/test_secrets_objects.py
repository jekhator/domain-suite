"""Tests for secret value objects."""

from __future__ import annotations

import dataclasses

import pytest

from monitoring_suite.security.services.constants import secrets as const
from monitoring_suite.security.services.secrets.secrets_objects import SecretValue


class TestSecretValue:
    """SecretValue masked secret storage."""

    def test_secret_value_frozen(self) -> None:
        """SecretValue is immutable after construction."""
        secret = SecretValue(_value="secret123")
        with pytest.raises(dataclasses.FrozenInstanceError):
            secret._value = "newvalue"  # type: ignore[misc]

    def test_get_returns_plaintext(self) -> None:
        """get returns the plaintext secret value."""
        plaintext = "my_secret_password"
        secret = SecretValue(_value=plaintext)
        assert secret.get() == plaintext

    def test_repr_masks_value(self) -> None:
        """repr returns masked value, never plaintext."""
        plaintext = "super_secret_key_12345"
        secret = SecretValue(_value=plaintext)
        assert repr(secret) == const.SECRET_VALUE_MASKED_REPR
        assert plaintext not in repr(secret)

    def test_repr_consistent(self) -> None:
        """repr is consistent across multiple calls."""
        secret = SecretValue(_value="secret1")
        assert repr(secret) == repr(secret)

    def test_repr_always_masked_different_values(self) -> None:
        """repr is identical regardless of secret content."""
        secret1 = SecretValue(_value="short")
        secret2 = SecretValue(_value="very_long_secret_value_here")
        assert repr(secret1) == repr(secret2)

    def test_equality_by_value(self) -> None:
        """SecretValues with same plaintext are equal."""
        s1 = SecretValue(_value="same_secret")
        s2 = SecretValue(_value="same_secret")
        assert s1 == s2

    def test_inequality_by_value(self) -> None:
        """SecretValues with different plaintext are not equal."""
        s1 = SecretValue(_value="secret1")
        s2 = SecretValue(_value="secret2")
        assert s1 != s2

    def test_empty_string_secret(self) -> None:
        """get and repr work with empty string secrets."""
        secret = SecretValue(_value="")
        assert secret.get() == ""
        assert repr(secret) == const.SECRET_VALUE_MASKED_REPR

    def test_multiline_secret(self) -> None:
        """SecretValue handles multiline secrets."""
        multiline = "line1\nline2\nline3"
        secret = SecretValue(_value=multiline)
        assert secret.get() == multiline
        assert repr(secret) == const.SECRET_VALUE_MASKED_REPR
