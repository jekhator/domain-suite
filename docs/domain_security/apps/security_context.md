# SecurityContext and SecurityContextManager

## Purpose

The security context spine provides an ambient, immutable pairing of a Principal (identity and scopes) and a tenant_id (isolation boundary). The SecurityContextManager stores this context in a ContextVar, making it available across async boundaries, thread pools, and call stacks without explicit parameter passing.

## Behavior

SecurityContext is a frozen dataclass holding a Principal and a tenant_id. Both are optional, allowing anonymous (no principal) and multi-tenant (no tenant_id) scenarios. SecurityContextManager uses Python's ContextVar to store the context, ensuring each async task and thread has its own stack of values.

The `bind()` method creates a temporary context scope, restoring the prior context on exit. The `set()` and `clear()` methods offer lower-level control for cases where manual token management is needed.

## Public Surface

### Principal

```python
Principal(
    id: str,
    roles: frozenset[str] = frozenset(),
    scopes: frozenset[str] = frozenset()
)
```

Immutable (frozen dataclass). Represents an authenticated identity with role and scope membership. All attributes are read-only after construction.

### SecurityContext

```python
SecurityContext(
    principal: Principal | None,
    tenant_id: str | None
)
```

Immutable (frozen dataclass). Pairs a principal (or None for anonymous) with a tenant boundary (or None for no tenant isolation).

### SecurityContextManager

```python
manager = SecurityContextManager()

# Store context, return reset token for later clear()
token: Token[SecurityContext | None] = manager.set(ctx)

# Retrieve current context, or None when unset
ctx: SecurityContext | None = manager.get()

# Temporarily bind context, restore prior on exit
with manager.bind(
    principal: Principal | None = None,
    tenant_id: str | None = None
) -> AbstractContextManager[None]:
    # Code here runs with the bound context
    pass

# Reset context to state before matching set() call
manager.clear(token: Token[SecurityContext | None]) -> None
```

## Constants

- `CONTEXT_VAR_NAME = "domain_security_context"` (ContextVar name, used by SecurityContextManager)

See `domain_security/context/constants/security_context.py`.

## Error Semantics

SecurityContextManager does not raise errors. The context objects are frozen dataclasses; assigning to a field raises `FrozenInstanceError` at runtime. Caller code that inspects `manager.get()` must handle None (no bound context).

## Example Usage

### Binding context in a request handler

```python
from domain_security import Principal, SecurityContext, SecurityContextManager

def handle_request(request):
    principal = Principal(
        id=request.user_id,
        roles=frozenset(request.roles),
        scopes=frozenset(request.scopes)
    )
    ctx = SecurityContext(principal=principal, tenant_id=request.tenant_id)
    
    manager = SecurityContextManager()
    with manager.bind(principal=principal, tenant_id=request.tenant_id):
        # All downstream calls see this context via manager.get()
        return process_request(request)
```

### Reading context in a service method

```python
from domain_security import SecurityContextManager

class DocumentService:
    def create_document(self, title: str):
        manager = SecurityContextManager()
        ctx = manager.get()
        
        if ctx is None:
            raise ValueError("No security context bound")
        
        principal = ctx.principal
        tenant_id = ctx.tenant_id
        
        # Use principal and tenant_id for authorization/auditing
        return {"id": "doc1", "title": title, "created_by": principal.id}
```

### Manual token management

```python
manager = SecurityContextManager()
principal = Principal(id="user1")
ctx = SecurityContext(principal=principal, tenant_id="tenant1")

token = manager.set(ctx)
try:
    # Context is active here
    assert manager.get() == ctx
finally:
    # Restore prior context
    manager.clear(token)
```

## See Also

- [Authorization with @requires](authz.md)
- [Tenant Isolation with @tenant_scoped](tenancy.md)
- [Error Types](security_errors.md)
