"""Secret value objects: the backend contract and the masked resolved value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from monitoring_suite.security.services.constants import secrets as const


class SecretsBackend(Protocol):
    """Contract for fetching a secret's plaintext value by name."""

    def fetch(self, name: str) -> str: ...


@dataclass(frozen=True, slots=True)
class SecretValue:
    """Resolved secret whose value never appears in repr output."""

    _value: str

    def get(self) -> str:
        """Return the plaintext secret value."""
        return self._value

    def __repr__(self) -> str:
        """Mask the secret value."""
        return const.SECRET_VALUE_MASKED_REPR
