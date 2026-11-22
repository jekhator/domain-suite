"""Secret references resolved at call time through a pluggable backend."""

from __future__ import annotations

from monitoring_suite.errors import wrap_errors
from monitoring_suite.security.errors.security_errors import SecretError
from monitoring_suite.security.services.constants import secrets as const
from monitoring_suite.security.services.secrets import secrets_objects as objs


class SecretRef:
    """Named reference to a secret, resolved lazily against a backend."""

    def __init__(self, name: str) -> None:
        """Store the secret name for later resolution."""
        self.name = name

    @wrap_errors(SecretError, capture=False)
    def resolve(self, backend: objs.SecretsBackend | None = None) -> objs.SecretValue:
        """Fetch the named secret from the backend and wrap it in a SecretValue."""
        if backend is None:
            raise SecretError(message=const.ERR_SECRETS_NO_BACKEND, secret_name=self.name)
        return objs.SecretValue(backend.fetch(self.name))
