# domain-security

Cross-cutting security concerns: authorization, tenancy, secrets, and context management.

## Overview

`domain-security` provides:

- **SecurityContext**: Ambient context with a principal (identity, roles, scopes) and a tenant boundary
- **Authorization checks**: Decorator-based permission enforcement
- **Tenant isolation**: Tenancy boundary validation
- **Secret management**: Lazy, masked secret resolution through a pluggable backend

## Quick Start

```python
from domain_security import Principal, SecurityContextManager, requires

# Describe the caller and bind the context for the duration of the request
principal = Principal(id="usr_123", scopes=frozenset(["documents.read"]))
manager = SecurityContextManager()

# Enforce authorization via decorator
@requires("documents.read")
def get_document(doc_id: str) -> dict:
    return {"doc": doc_id, "requested_by": manager.get().principal.id}

with manager.bind(principal=principal, tenant_id="org_abc"):
    print(get_document("doc_1"))
```

## Public API

- **`SecurityContext`**: Immutable pairing of a principal and a tenant id
- **`SecurityContextManager`**: ContextVar-based set, get, bind and clear of the ambient context
- **`Principal`**: Identity with `id`, `roles` and `scopes`
- **`requires`**: Decorator for permission checks
- **`tenant_scoped`**: Decorator for tenant isolation checks
- **`Authorizer`**: Scope-based authorization policy engine
- **`Permission`**, **`PolicyDecision`**: Authorization models
- **`SecretRef`**, **`SecretValue`**: Secret reference and masked resolved value
- Security error classes: `SecurityError`, `AuthzError`, `TenancyError`, `SecretError`, `SecurityDeclarationError`

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
- **[flow-trace.md](architecture/flow-trace.md)**: Call-level trace of the enforcement path
- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before domain-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Request Context Setup (e.g., Django Middleware)

```python
from domain_security import Principal, SecurityContextManager

manager = SecurityContextManager()

class SecurityContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract the identity from the verified token or session
        principal = Principal(
            id=request.user.id,
            roles=frozenset(request.roles),
            scopes=frozenset(request.scopes),
        )
        with manager.bind(principal=principal, tenant_id=request.tenant.id):
            return self.get_response(request)
```

### Multi-Tenant Data Access

```python
from domain_security import SecurityContextManager, tenant_scoped

manager = SecurityContextManager()

@tenant_scoped("tenant_id")
def get_tenant_data(tenant_id: str) -> dict:
    # The decorator has already checked tenant_id against the bound context
    return {"tenant": tenant_id}

with manager.bind(tenant_id="org_abc"):
    print(get_tenant_data("org_abc"))
```

## Integration with domain-aspects

Use the `Requires` or `TenantScoped` aspects for composable security:

```python
from domain_aspects import aspects, Requires, TenantScoped

@aspects(
    Requires(permission="documents.read"),
    TenantScoped(param_name="tenant_id"),
)
def get_document(doc_id: str, tenant_id: str):
    pass
```

## Next Steps

- Read the [main domain-suite README](../../README.md) for installation and examples
- Choose a feature from the list above and read its detailed documentation
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
