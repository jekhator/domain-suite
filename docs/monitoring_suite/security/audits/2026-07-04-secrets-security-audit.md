# Security Audit: secrets

**Audited**: 2026-07-04  
**Feature**: Secret value management and lazy resolution via backend protocol  
**Scope**: SecretValue masking; SecretRef resolution; wrap_errors capture=False; backend contract

## Input Handling and Validation Surface

### SecretValue Value Object

**SecretValue** (monitoring_suite/security/services/secrets/secrets_objects.py:17-29):
- Frozen dataclass with slots.
- Field: `_value: str` (plaintext secret, private by underscore naming).
- Constructor accepts `_value: str` from caller (no validation); caller responsibility to provide correct plaintext.
- Immutability ensures the stored value cannot be mutated or replaced post-creation.

### SecretRef Lazy Resolution

**SecretRef** (monitoring_suite/security/services/secrets/secrets_client.py:12-27):
- Mutable class (stores `name: str` in __init__).
- resolve() method (line 19-27) accepts optional `backend: SecretsBackend | None`.
- Step 1 (line 22-26): If backend is None, raise SecretError immediately (fail-safe).
- Step 2 (line 27): Call backend.fetch(self.name) to retrieve plaintext.
- Step 3 (line 27): Wrap fetched plaintext in SecretValue(backend.fetch(self.name)).

**Input Validation**: No validation of name. Caller constructs with a secret name; backend fetch fails if name is unknown.

### SecretsBackend Protocol

**SecretsBackend** (monitoring_suite/security/services/secrets/secrets_objects.py:11-14):
- Protocol defining contract: `def fetch(self, name: str) -> str`.
- Backend implementations are pluggable (AWS Secrets Manager, HashiCorp Vault, environment variables, etc.).
- This module does not validate backend implementation; it trusts the protocol contract.

## Secret Hygiene

### Plaintext Handling

- `SecretValue._value` stores plaintext but is private (underscore convention).
- `get()` method (line 23-25) explicitly returns plaintext; callers must request it.
- No implicit plaintext exposure; plaintext access is opt-in via get().

### Masked __repr__

**__repr__** (line 27-29):
- Returns constant `const.SECRET_VALUE_MASKED_REPR` (value: "<SecretValue ***>").
- If SecretValue is printed, logged, or converted to string in default repr context, plaintext is masked.
- Prevents accidental log leakage via f-strings, print(), or debug output.

**Implication**: Developers using SecretValue in logs/output get safe output by default.

### Wrap Errors with capture=False

**resolve() Decorator** (line 19):
- `@wrap_errors(SecretError, capture=False)`.
- `capture=False` (from monitoring_suite.errors library) means: if backend.fetch() raises an exception, that exception's arguments are NOT captured in the wrapped SecretError context.
- This prevents plaintext values from leaking into error context if backend raises with the secret in its message.

**Implication**: Backend failures (e.g., "secret 'db_password' value is 'xyz123'") are wrapped with safe message only, not the backend's raw exception arguments.

### No Logging of Plaintext

- resolve() does not log self.name or backend.fetch() result.
- Caller obtains SecretValue, calls get(), and uses plaintext; logging that plaintext is caller's responsibility (and discouraged).
- Module itself does not produce any secret-bearing logs.

## Deny-by-Default Posture

**Backend Requirement** (line 22-26):
- If backend is None, raises SecretError immediately.
- No default backend, no implicit fallback.
- Caller must provide a backend; absence denies access.

**Error-on-Fetch**: If backend.fetch(name) fails, the exception is caught by @wrap_errors and re-raised as SecretError with safe message (no capture of backend exception args).

## Error-Content Review

**SecretError Construction** (line 23-26):
- `message=const.ERR_SECRETS_NO_BACKEND` (constant string "no secrets backend provided").
- `secret_name=self.name` (secret name/identifier, safe metadata for debugging).

**With capture=False**: Backend errors are wrapped with cause preserved but message replaced with safe constant, so backend's raw exception message (which might contain the plaintext) does not leak into the wrapped error.

**Error Safety**: Error does not contain plaintext value; only secret name (identifier) and safe message.

## Dependency Surface

- **stdlib**: dataclasses, typing.
- **monitoring_suite.errors**: wrap_errors decorator (with capture=False option).
- **No secrets backend dependency**: Backend is pluggable via protocol; no hardcoded AWS SDK, Vault client, or environment-variable inspection.

## Verdict

**PASS**

Masked __repr__, plaintext-only-via-explicit-get(), wrap_errors(capture=False), no logging of plaintext, and fail-safe backend requirement form a sound secret handling surface. Frozen SecretValue immutability and protocol-based backend pluggability prevent plaintext exposure.
