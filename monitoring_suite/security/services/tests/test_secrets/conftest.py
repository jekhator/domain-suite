"""Fixtures for secrets tests."""

from __future__ import annotations

import pytest


class FakeSecretsBackend:
    """Fake backend for testing secret resolution."""

    def __init__(self, secrets: dict[str, str] | None = None) -> None:
        """Store secrets in memory."""
        self.secrets = secrets or {}

    def fetch(self, name: str) -> str:
        """Return the secret value or raise KeyError."""
        if name not in self.secrets:
            raise KeyError(f"secret not found: {name}")
        return self.secrets[name]


@pytest.fixture
def fake_backend() -> FakeSecretsBackend:  # noqa: R004
    """Create a fake secrets backend."""
    return FakeSecretsBackend(
        {"db_password": "super_secret_123", "api_key": "key_abc_xyz"}
    )


@pytest.fixture
def failing_backend() -> FakeSecretsBackend:  # noqa: R004
    """Create a backend with no secrets configured."""
    return FakeSecretsBackend({})
