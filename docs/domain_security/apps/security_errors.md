# Error Types and Semantics

## Purpose

The security domain defines a typed error hierarchy for authorization, tenancy, and secrets failures. All errors subclass DomainError from the domain-errors package, providing structured logging, HTTP status codes, and typed context parameters.

## Behavior

All security errors:
- Subclass DomainError for integration with domain-errors structured logging.
- Preserve __cause__ when wrapping exceptions (e.g., backend fetch failures wrapped as SecretError).
- Carry context parameters for debugging (permission value, tenant_id, secret_name, etc.).
- Set http_status for HTTP response mapping (403 for authorization/tenancy, 500 for secrets).
- Have a retryable flag (all security errors are not retryable).

Errors are raised by:
- @requires decorator when the principal lacks required scope.
- @tenant_scoped decorator when the context's tenant_id mismatches.
- Authorizer.require() when a permission check fails.
- SecretRef.resolve() when a backend is unavailable or fetch fails.

## Public Surface

### SecurityError (base class)

```python
class SecurityError(DomainError):
    domain = "security"
    code = "security_error"
    http_status = 403
    retryable = False
    default_message = "Security constraint violated."
```

Base exception for all security-domain failures.

### AuthzError

```python
class AuthzError(SecurityError):
    code = "authz_denied"
    default_message = "Permission denied."
```

Permission denied by authorization policy. Raised by:
- @requires decorator when scope check fails.
- Authorizer.require() when permission is denied.

Context parameters:
- `permission: str` (the permission that was denied)

### TenancyError

```python
class TenancyError(SecurityError):
    code = "tenant_boundary_violation"
    default_message = "Tenant boundary violation."
```

Operation crossed or lacked a tenant boundary. Raised by:
- @tenant_scoped decorator when tenant_id mismatches or is missing.
- TenancyGuard.check() when boundary is violated.

Context parameters:
- `tenant_id: str` (the target tenant_id)
- `context_tenant_id: str` (optional, the bound context's tenant_id if available)

### SecurityDeclarationError

```python
class SecurityDeclarationError(SecurityError):
    code = "security_declaration_failed"
    http_status = 500
    default_message = "Security decorator declaration failed."
```

Decorator declaration-time validation failure. Raised when @tenant_scoped is applied to a class that has a public method lacking the named tenant parameter. Context parameters: `method_name: str`, `param_name: str`.

### SecretError

```python
class SecretError(SecurityError):
    code = "secret_access_failed"
    http_status = 500
    default_message = "Secret access failed."
```

Secret resolution or access failure. Raised by:
- SecretRef.resolve() when backend is None or fetch fails.

The error preserves __cause__ with the original backend exception. Set http_status to 500 (server error) rather than 403 (forbidden) because secrets failure indicates a system misconfiguration, not a client permission issue.

Context parameters:
- `secret_name: str` (the secret identifier)

## Constants

Security errors use message templates from their respective concern modules:

**Authorization (authz):**
- `ERR_AUTHZ_NO_PRINCIPAL = "no authenticated principal"`
- `ERR_AUTHZ_MISSING_SCOPE = "missing scope {scope}"`

**Tenancy (tenancy):**
- `ERR_TENANCY_NO_TENANT_BOUND = "no tenant bound in security context"`
- `ERR_TENANCY_BOUNDARY_VIOLATION = "tenant boundary violation"`

**Secrets (secrets):**
- `ERR_SECRETS_NO_BACKEND = "no secrets backend provided"`

**Tenant-scoped decorator (tenant_scoped):**
- `ERR_TENANT_SCOPED_UNBOUND_SELF = "self.tenant_id requires a bound method call"`
- `ERR_TENANT_SCOPED_NULL_TENANT = "tenant argument resolved to None"`
- `ERR_TENANT_SCOPED_PARAM_MISSING = "tenant parameter missing from call"`

See the respective concern modules for imports.

## Error Semantics

### AuthzError

Raised when:
- No SecurityContext is bound (anonymous).
- The principal's scopes do not include the required permission.

HTTP status: 403 Forbidden.

Retryable: No. Authorization checks are deterministic; re-running will fail the same way.

### TenancyError

Raised when:
- The ambient context has no tenant_id bound (None).
- The context's tenant_id differs from the target tenant_id.
- The tenant parameter cannot be extracted (missing parameter, unbound self) or resolves to None.

HTTP status: 403 Forbidden.

Retryable: No. Tenant boundaries are enforce-or-fail; retries will hit the same boundary.

### SecretError

Raised when:
- Backend is None.
- Backend.fetch() raises any exception.

HTTP status: 500 Internal Server Error.

Retryable: Depends on the underlying backend failure. The library marks SecretError as non-retryable by default, but callers should inspect __cause__ to determine if a transient backend issue warrants a retry.

## Example Usage

### Catching and inspecting errors

```python
from domain_security import requires, AuthzError, Principal, SecurityContextManager

@requires("documents:write")
def create_document(title: str) -> dict:
    return {"id": "doc1", "title": title}

manager = SecurityContextManager()
principal = Principal(id="user1", scopes=frozenset(["documents:read"]))

with manager.bind(principal=principal, tenant_id="tenant1"):
    try:
        create_document("My Doc")
    except AuthzError as e:
        print(f"Error code: {e.code}")  # "authz_denied"
        print(f"HTTP status: {e.http_status}")  # 403
        print(f"Message: {e.message}")
        print(f"Permission: {e.context.get('permission')}")  # Extracted from context
```

### Handling tenancy errors

```python
from domain_security import tenant_scoped, TenancyError, Principal, SecurityContextManager

@tenant_scoped("tenant_id")
def delete_document(doc_id: str, tenant_id: str) -> None:
    pass

manager = SecurityContextManager()
principal = Principal(id="user1")

with manager.bind(principal=principal, tenant_id="acme"):
    try:
        delete_document("doc1", "other")
    except TenancyError as e:
        print(f"Error code: {e.code}")  # "tenant_boundary_violation"
        print(f"HTTP status: {e.http_status}")  # 403
        print(f"Message: {e.message}")
        print(f"Target tenant: {e.context.get('tenant_id')}")  # "other"
        print(f"Context tenant: {e.context.get('context_tenant_id')}")  # "acme"
```

### Handling secret errors with root cause

```python
from domain_security import SecretRef, SecretError

# Case 1: No backend provided
ref = SecretRef("api_key")
try:
    secret = ref.resolve(backend=None)
except SecretError as e:
    print(f"Error code: {e.code}")  # "secret_access_failed"
    print(f"HTTP status: {e.http_status}")  # 500
    print(f"Message: {e.message}")
    print(f"Secret name: {e.context.get('secret_name')}")  # "api_key"

# Case 2: Backend fails with an exception
class FailingBackend:
    def fetch(self, name: str) -> str:
        raise ConnectionError("Vault unreachable")

ref2 = SecretRef("db_password")
try:
    secret = ref2.resolve(FailingBackend())
except SecretError as e:
    print(f"Error code: {e.code}")  # "secret_access_failed"
    print(f"HTTP status: {e.http_status}")  # 500
    print(f"Root cause: {type(e.__cause__).__name__}")  # "ConnectionError"
    
    # Decide whether to retry based on root cause
    if isinstance(e.__cause__, ConnectionError):
        print("Backend is unreachable; retrying may help")
```

### Logging errors with structured context

```python
import logging
from domain_security import requires, AuthzError, Principal, SecurityContextManager

logger = logging.getLogger(__name__)

@requires("admin")
def perform_admin_action() -> None:
    logger.info("Admin action executed")

manager = SecurityContextManager()
principal = Principal(id="user1", scopes=frozenset(["user:read"]))

with manager.bind(principal=principal, tenant_id="tenant1"):
    try:
        perform_admin_action()
    except AuthzError as e:
        # domain-errors integration logs with structured context
        logger.error(
            "Authorization denied",
            extra={
                "error_code": e.code,
                "http_status": e.http_status,
                "permission": e.context.get("permission"),
                "user_id": principal.id,
                "tenant_id": "tenant1"
            }
        )
```

## See Also

- [Authorization](authz.md)
- [Tenant Isolation](tenancy.md)
- [Secrets Management](secrets.md)
- [domain-errors package](https://github.com/jekhator/domain-errors)
