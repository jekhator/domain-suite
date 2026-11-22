# Security Audit: security_errors

**Audited**: 2026-07-04  
**Feature**: Typed security error hierarchy and structured error context  
**Scope**: SecurityError, AuthzError, TenancyError, SecretError base classes; DomainError contract

## Input Handling and Validation Surface

### Error Class Hierarchy

**SecurityError** (monitoring_suite/security/errors/security_errors.py:8-15):
- Base class inheriting from DomainError.
- Class attributes: `domain = "security"`, `code = "security_error"`, `http_status = 403`, `retryable = False`, `default_message = "Security constraint violated."`.
- No constructor validation; DomainError handles initialization.

**AuthzError** (line 18-22):
- Subclass of SecurityError.
- Attributes: `code = "authz_denied"`, `default_message = "Permission denied."`, http_status inherited (403).

**TenancyError** (line 25-29):
- Subclass of SecurityError.
- Attributes: `code = "tenant_boundary_violation"`, `default_message = "Tenant boundary violation."`, http_status inherited (403).

**SecretError** (line 32-37):
- Subclass of SecurityError.
- Attributes: `code = "secret_access_failed"`, `http_status = 500` (overrides parent 403), `default_message = "Secret access failed."`.

### DomainError Contract

- Parent class (from monitoring_suite.errors library).
- Accepts keyword arguments for structured context (e.g., `message=`, `permission=`, `tenant_id=`).
- Constructs structured logging payload (audit trail).
- No validation of context fields; callers pass safe metadata.

## Secret Hygiene

**Error Context Policy**: All error context fields are audit metadata (names, identifiers, permission names). Callers must not pass secrets, plaintext passwords, or PII as context fields.

**Examples**:
- AuthzError(message=..., permission=...) - permission is a string name, not a secret.
- TenancyError(message=..., tenant_id=..., context_tenant_id=...) - both are identifiers, not secrets.
- SecretError(message=..., secret_name=...) - secret_name is an identifier, not the plaintext value.

**No Implicit Masking**: These error classes do not mask or sanitize context fields. If a caller passes a secret as a context field, the error will log it. This is a caller-side responsibility.

**Error Message Default**: Each error class has a `default_message` (e.g., "Permission denied.") that does not contain secret data. Callers may override message with a constant (see authz, tenancy, secrets audits).

## Deny-by-Default Posture

**Error as Denial Signal**: All three subclasses (AuthzError, TenancyError, SecretError) are exceptions. When raised, they interrupt execution and signal denial to caller.

**HTTP Status Codes**:
- SecurityError, AuthzError, TenancyError: http_status = 403 (Forbidden).
- SecretError: http_status = 500 (Internal Server Error).

**Rationale**: AuthzError and TenancyError are policy denials (client should not retry); SecretError is a backend failure (internal error, may be retryable).

**retryable = False**: All inherit from SecurityError with retryable = False. This signals that client-side auth/tenancy failures should not be retried.

## Error-Content Review

### Error Construction Patterns

**Authz** (authz_client.py:35-38):
```python
raise AuthzError(
    message=decision.reason,
    permission=permission.value,
)
```
- message: Safe constant or formatted string with permission name only.
- permission: Permission name string.

**Tenancy** (tenancy_client.py:18-27):
```python
raise TenancyError(
    message=const.ERR_TENANCY_NO_TENANT_BOUND,
    tenant_id=tenant_id,
)
# or
raise TenancyError(
    message=const.ERR_TENANCY_BOUNDARY_VIOLATION,
    tenant_id=tenant_id,
    context_tenant_id=ctx.tenant_id,
)
```
- message: Safe constant string.
- tenant_id, context_tenant_id: Identifiers (safe metadata for audit).

**Secrets** (secrets_client.py:23-26):
```python
raise SecretError(
    message=const.ERR_SECRETS_NO_BACKEND,
    secret_name=self.name,
)
```
- message: Safe constant string.
- secret_name: Secret identifier/name string (not the plaintext value).

### Error Context Safety

All error fields are designed to be audit-safe. The error hierarchy itself does not expose secrets, principal state, or request payloads.

**Caller Responsibility**: If a caller constructs an error with a secret in the context, the error will log it. This is not a bug in the error class; it is a bug in the caller's usage.

## Dependency Surface

- **stdlib only**: No external imports except monitoring_suite.errors.
- **monitoring_suite.errors**: DomainError base class.
- **No error-specific logic**: Error classes are data containers only; enforcement logic lives in authz_client, tenancy_client, and secrets_client.

## Verdict

**PASS**

Structured error hierarchy (SecurityError base, three typed subclasses), safe default messages, http_status codes aligned with denial policy (403 for auth/tenancy, 500 for backend failure), and retryable = False form a sound error interface. No secret masking or validation in error class itself; context safety is caller responsibility (enforced by authz, tenancy, and secrets modules). Error metadata (permission, tenant_id, secret_name) are identifiers only, not secrets.
