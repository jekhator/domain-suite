# monitoring_suite.security

Cross-cutting security concerns: authorization, tenancy, secrets, and context management.

## Overview

`monitoring_suite.security` provides:

- **SecurityContext**: Request-scoped context with principal, tenant, and claims
- **Authorization checks**: Decorator-based permission enforcement
- **Tenant isolation**: Tenancy boundary validation
- **Secret management**: Credential resolution from external sources (environment, vaults, etc.)

## Quick Start

```python
from monitoring_suite.security import SecurityContext, SecurityContextManager, requires

# Set security context (typically from JWT or session)
ctx = SecurityContext(
    user_id="usr_123",
    tenant_id="org_abc",
    claims={"role": "admin", "scope": "documents.read"}
)
SecurityContextManager.set(ctx)

# Enforce authorization via decorator
@requires(permission="documents.read")
def get_document(doc_id: str):
    ctx = SecurityContextManager.get()
    return {"user": ctx.principal.user_id, "doc": doc_id}
```

## Public API

- **`SecurityContext`**: Principal identity, tenant, and claims container
- **`SecurityContextManager`**: ContextVar-based context manager for request scope
- **`Principal`**: Principal identity details (user_id, tenant_id)
- **`requires`**: Decorator for permission checks
- **`tenant_scoped`**: Decorator for tenant isolation checks
- **`Authorizer`**: Authorization policy engine
- **`Permission`**, **`PolicyDecision`**: Authorization models
- **`SecretRef`**, **`SecretValue`**: Secret reference and resolution
- Security error classes: `AuthzError`, `TenancyError`, `SecretError`, etc.

## Features

### Per-Feature Documentation

Detailed documentation for each feature:

- **[security_context.md](apps/security_context.md)**: Context management and principal identity
- **[authz.md](apps/authz.md)**: Authorization policy engine
- **[requires.md](apps/requires.md)**: Permission enforcement decorator
- **[tenant_scoped.md](apps/tenant_scoped.md)**: Tenant isolation decorator
- **[tenancy.md](apps/tenancy.md)**: Tenant boundary validation
- **[secrets.md](apps/secrets.md)**: Secret credential management
- **[security_errors.md](apps/security_errors.md)**: Security-specific exception hierarchy

### Architecture & Design

- **[diagrams.md](apps/diagrams.md)**: Visual guides to authorization and context flow
- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before monitoring-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Request Context Setup (e.g., Django Middleware)

```python
from monitoring_suite.security import SecurityContext, SecurityContextManager

class SecurityContextMiddleware:
    def __call__(self, request):
        # Extract from JWT or session
        user_id = request.user.id
        tenant_id = request.tenant.id
        claims = jwt.decode(request.auth_header)
        
        ctx = SecurityContext(
            user_id=user_id,
            tenant_id=tenant_id,
            claims=claims
        )
        SecurityContextManager.set(ctx)
```

### Multi-Tenant Data Access

```python
from monitoring_suite.security import tenant_scoped

@tenant_scoped(param_name="tenant_id")
def get_tenant_data(tenant_id: str):
    ctx = SecurityContextManager.get()
    # Verify tenant_id matches context
    return fetch_data_for_tenant(tenant_id)
```

## Integration with monitoring_suite.aspects

Use the `@Requires` or `@TenantScoped` aspects for composable security:

```python
from monitoring_suite.aspects import aspects, Requires, TenantScoped

@aspects(
    Requires(permission="documents.read"),
    TenantScoped(param_name="tenant_id"),
)
def get_document(doc_id: str, tenant_id: str):
    pass
```

## Next Steps

- Read the [main monitoring-suite README](../../README.md) for installation and examples
- Choose a feature from the list above and read its detailed documentation
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
