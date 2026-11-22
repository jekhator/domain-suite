# Secrets Management with SecretRef and SecretValue

## Purpose

SecretRef provides lazy, call-time secret resolution against a pluggable backend. Secrets are never stored as string literals in code. SecretValue wraps a resolved secret and masks its repr to prevent accidental logging or printing of sensitive data.

## Behavior

SecretRef holds a name (identifier) and delegates resolution to a SecretsBackend at call time. If the backend is not provided or raises an exception, SecretRef.resolve() wraps the error as SecretError with the original exception preserved in __cause__.

SecretValue wraps the resolved plaintext and exposes it via get(). Its __repr__ returns a masked token `<SecretValue ***>` to prevent accidental exposure through logging or debugging output.

## Public Surface

### SecretsBackend Protocol

```python
class SecretsBackend(Protocol):
    def fetch(self, name: str) -> str:
        # Return the plaintext secret value by name.
        # Raise any exception on failure (e.g., KeyError, backend unreachable).
        ...
```

Any object implementing this protocol can be passed to SecretRef.resolve().

### SecretRef

```python
ref = SecretRef(name: str)

# Lazy resolution at call time; raises SecretError on failure.
secret: SecretValue = ref.resolve(backend: SecretsBackend | None = None) -> SecretValue
```

- `name: str` (instance attribute, secret identifier)
- `resolve()` is wrapped with @wrap_errors(SecretError, capture=False), meaning exceptions from the backend are re-raised as SecretError with __cause__ preserved.

### SecretValue

```python
# Resolved secret; immutable (frozen dataclass).
secret = SecretValue(_value: str)

# Return the plaintext secret value.
plaintext: str = secret.get() -> str

# Masked representation (never shows the actual value).
repr(secret)  # <SecretValue ***>
```

- `_value: str` (private, internal storage)
- `get()` returns the plaintext value

## Constants

- `SECRET_VALUE_MASKED_REPR = "<SecretValue ***>"` (the masked repr token)
- `ERR_SECRETS_NO_BACKEND = "no secrets backend provided"` (raised when backend is None)

See `monitoring_suite/security/services/constants/secrets.py`.

## Error Semantics

`resolve()` raises SecretError if:
- Backend is None.
- Backend.fetch() raises any exception.

All exceptions are wrapped as SecretError with the original exception preserved in __cause__. This allows callers to inspect the root cause while the top-level error is typed and logged uniformly.

See [Error Types](security_errors.md) for SecretError details.

## Example Usage

### Basic secret resolution

```python
from monitoring_suite.security import SecretRef, SecretError

class MySecretsBackend:
    def fetch(self, name: str) -> str:
        secrets = {
            "api_key": "sk_live_abc123",
            "db_password": "mysecure"
        }
        if name not in secrets:
            raise KeyError(f"Secret not found: {name}")
        return secrets[name]

ref = SecretRef("api_key")
backend = MySecretsBackend()

try:
    secret = ref.resolve(backend)
    api_key = secret.get()
    print(f"API key fetched (length: {len(api_key)})")
    # Never print repr(secret); it's safe:
    print(f"Secret masked: {repr(secret)}")
except SecretError as e:
    print(f"Secret resolution failed: {e.message}")
    print(f"Root cause: {e.__cause__}")
```

### Environment-based backend

```python
import os
from monitoring_suite.security import SecretRef

class EnvSecretsBackend:
    def fetch(self, name: str) -> str:
        value = os.environ.get(name)
        if value is None:
            raise KeyError(f"Environment variable {name} not found")
        return value

ref = SecretRef("DATABASE_URL")
backend = EnvSecretsBackend()

try:
    secret = ref.resolve(backend)
    db_url = secret.get()
    # Use db_url to connect
except SecretError as e:
    # Log error safely; repr(secret) is masked
    print(f"Cannot access database: {e.message}")
```

### Vault-like backend

```python
from monitoring_suite.security import SecretRef

class VaultSecretsBackend:
    def __init__(self, vault_url: str, token: str):
        self.vault_url = vault_url
        self.token = token
    
    def fetch(self, name: str) -> str:
        # Make request to Vault API
        # This is pseudo-code; actual implementation would use requests or httpx
        import requests
        try:
            resp = requests.get(
                f"{self.vault_url}/v1/secret/data/{name}",
                headers={"X-Vault-Token": self.token}
            )
            resp.raise_for_status()
            return resp.json()["data"]["data"]["value"]
        except requests.RequestException as e:
            raise RuntimeError(f"Vault fetch failed: {e}")

# Usage
ref = SecretRef("my_app/database_password")
backend = VaultSecretsBackend("https://vault.example.com", "my_token")

try:
    secret = ref.resolve(backend)
    password = secret.get()
except SecretError as e:
    # Root cause is in e.__cause__
    print(f"Cannot resolve secret: {e.message}")
```

### Multiple secrets with a factory

```python
from monitoring_suite.security import SecretRef

class AppSecrets:
    def __init__(self, backend):
        self.backend = backend
        self.api_key = SecretRef("api_key")
        self.db_password = SecretRef("db_password")
    
    def resolve_all(self):
        return {
            "api_key": self.api_key.resolve(self.backend).get(),
            "db_password": self.db_password.resolve(self.backend).get()
        }

# Usage
backend = MySecretsBackend()
secrets = AppSecrets(backend)
resolved = secrets.resolve_all()
print(f"Secrets loaded (count: {len(resolved)})")
```

## See Also

- [Error Types](security_errors.md)
