# Authorization with Authorizer and @requires

## Purpose

Authorization enforces that an authenticated principal holds the required permission. The Authorizer class implements scope-based policy: a permission is granted only if the principal's scopes include the requested permission. Subclass Authorizer to implement richer policies (attribute-based, role-based, database-backed).

The @requires decorator applies authorization checks declaratively to service methods, reading the ambient SecurityContext and enforcing the required scope before the method runs.

## Behavior

The default Authorizer denies access if:
- No principal is bound (anonymous request).
- The principal's scopes do not include the requested permission.

Both cases return a PolicyDecision with `allowed=False` and a denial reason. Calling `require()` raises AuthzError if the decision is denied.

The @requires decorator fetches the ambient SecurityContext and calls the authorizer's `require()` method. No context or denial raises AuthzError before the decorated method runs.

## Public Surface

### Permission

```python
Permission(value: str)
```

Immutable (frozen dataclass). Identifies a permission to be checked against a principal's scopes.

### PolicyDecision

```python
PolicyDecision(
    allowed: bool,
    reason: str | None = None
)
```

Immutable (frozen dataclass). The outcome of an authorization check, with an optional denial reason.

### Authorizer

```python
authorizer = Authorizer()

# Evaluate the permission; return a decision without raising.
decision: PolicyDecision = authorizer.check(
    ctx: SecurityContext,
    permission: Permission
) -> PolicyDecision

# Enforce the permission; raise AuthzError if denied.
authorizer.require(
    ctx: SecurityContext,
    permission: Permission
) -> None
```

## Constants

- `ERR_AUTHZ_NO_PRINCIPAL = "no authenticated principal"` (returned when principal is None)
- `ERR_AUTHZ_MISSING_SCOPE = "missing scope {scope}"` (returned when scope not found, {scope} is the permission value)

See `monitoring_suite/security/services/constants/authz.py`.

## Error Semantics

`check()` does not raise; it returns a PolicyDecision with allowed=False and a reason string.

`require()` raises AuthzError if the decision is denied. The error carries the permission value for logging and debugging.

See [Error Types](security_errors.md) for AuthzError details.

## Example Usage

### Check without raising

```python
from monitoring_suite.security import Authorizer, Permission, SecurityContext, Principal

principal = Principal(id="user1", scopes=frozenset(["docs:read", "docs:write"]))
ctx = SecurityContext(principal=principal, tenant_id="tenant1")

authorizer = Authorizer()

# Check if principal can read documents
decision = authorizer.check(ctx, Permission("docs:read"))
if decision.allowed:
    print("Read permitted")
else:
    print(f"Read denied: {decision.reason}")

# Check a missing scope
decision = authorizer.check(ctx, Permission("admin"))
print(f"Admin allowed: {decision.allowed}")  # False
print(f"Reason: {decision.reason}")  # "missing scope admin"
```

### Enforce with require()

```python
from monitoring_suite.security import Authorizer, Permission, SecurityContext, Principal, AuthzError

principal = Principal(id="user1", scopes=frozenset(["docs:read"]))
ctx = SecurityContext(principal=principal, tenant_id="tenant1")

authorizer = Authorizer()

# This succeeds
authorizer.require(ctx, Permission("docs:read"))
print("Read permission confirmed")

# This raises AuthzError
try:
    authorizer.require(ctx, Permission("docs:write"))
except AuthzError as e:
    print(f"Write denied: {e.message}")
```

### Custom authorizer with role-based policy

```python
from monitoring_suite.security import Authorizer, Permission, PolicyDecision, SecurityContext

class RoleBasedAuthorizer(Authorizer):
    # Map roles to permissions
    ROLE_PERMISSIONS = {
        "admin": {"*"},
        "editor": {"docs:read", "docs:write"},
        "viewer": {"docs:read"}
    }
    
    def check(self, ctx: SecurityContext, permission: Permission) -> PolicyDecision:
        if ctx.principal is None:
            return PolicyDecision(allowed=False, reason="no authenticated principal")
        
        # Check if any role grants the permission
        for role in ctx.principal.roles:
            perms = self.ROLE_PERMISSIONS.get(role, set())
            if "*" in perms or permission.value in perms:
                return PolicyDecision(allowed=True)
        
        return PolicyDecision(
            allowed=False,
            reason=f"role {list(ctx.principal.roles)[0] if ctx.principal.roles else 'unknown'} does not grant {permission.value}"
        )
```

## See Also

- [SecurityContext](security_context.md)
- [@requires decorator](requires.md)
- [Error Types](security_errors.md)
