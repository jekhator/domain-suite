# @requires Decorator

## Purpose

The @requires decorator enforces scope-based permission checks on service methods. It reads the ambient SecurityContext and applies the configured Authorizer's require() method before the decorated function runs.

## Behavior

The @requires decorator:
1. Reads the ambient SecurityContext via SecurityContextManager.
2. If no context is bound, treats the call as anonymous (principal=None, tenant_id=None).
3. Calls the authorizer's require() method with the permission.
4. Raises AuthzError if the permission is denied.
5. Calls the decorated function only if authorization succeeds.

## Public Surface

### @requires decorator (module-level instance)

```python
from domain_security import requires

# Apply to a function or method
@requires("permission_name")
def my_method(arg1: str, arg2: int) -> str:
    return f"Result for {arg1}"

# The decorator is applied as `@requires("permission_name")`; the permission is a string argument to the module-level instance.
# Raises AuthzError before the method runs if the check fails.
```

## Constants

No constants specific to @requires. The decorator uses the authorizer and context constants; see [authz.md](authz.md) and [security_context.md](security_context.md).

## Error Semantics

The @requires decorator raises AuthzError if:
- No SecurityContext is bound (anonymous).
- The bound principal has no scopes.
- The required permission is not in the principal's scopes.

See [Error Types](security_errors.md) for AuthzError details.

## Example Usage

### Basic scope check

```python
from domain_security import requires, AuthzError, Principal, SecurityContextManager

@requires("documents:read")
def get_document(doc_id: str) -> dict:
    return {"id": doc_id, "content": "..."}

# Success case: principal has the required scope
manager = SecurityContextManager()
principal = Principal(
    id="user1",
    scopes=frozenset(["documents:read", "documents:write"])
)

with manager.bind(principal=principal, tenant_id="tenant1"):
    doc = get_document("doc1")
    print(f"Retrieved: {doc}")

# Failure case: principal lacks the scope
principal_limited = Principal(
    id="user2",
    scopes=frozenset(["documents:read"])  # Holds only the scope get_document needs
)

with manager.bind(principal=principal_limited, tenant_id="tenant1"):
    doc = get_document("doc2")  # Succeeds: get_document requires documents:read
    print(f"Retrieved: {doc}")

with manager.bind(principal=Principal(id="user3"), tenant_id="tenant1"):
    try:
        get_document("doc3")  # No scopes at all: denied
    except AuthzError as e:
        print(f"Denied: {e.message}")
```

### Multiple decorators

```python
from domain_security import requires, tenant_scoped, Principal, SecurityContextManager

@requires("documents:write")
@tenant_scoped("tenant_id")
def delete_document(doc_id: str, tenant_id: str) -> None:
    print(f"Document {doc_id} deleted")

# Both checks run: first @tenant_scoped (inner), then @requires (outer)
manager = SecurityContextManager()
principal = Principal(
    id="user1",
    scopes=frozenset(["documents:write"])
)

with manager.bind(principal=principal, tenant_id="acme"):
    delete_document("doc1", "acme")
```

### Class method with @requires

```python
from domain_security import requires, Principal, SecurityContextManager

class DocumentService:
    @requires("documents:write")
    def create_document(self, title: str, content: str) -> dict:
        return {
            "id": "doc1",
            "title": title,
            "content": content
        }

manager = SecurityContextManager()
principal = Principal(id="user1", scopes=frozenset(["documents:write"]))

with manager.bind(principal=principal, tenant_id="tenant1"):
    service = DocumentService()
    doc = service.create_document("My Doc", "Hello")
    print(f"Created: {doc}")
```

### Complex scope names

```python
from domain_security import requires, Principal, SecurityContextManager

# Use hierarchical scope names
@requires("admin:system:configure")
def configure_system() -> None:
    print("System configured")

manager = SecurityContextManager()
principal = Principal(
    id="admin1",
    roles=frozenset(["sysadmin"]),
    scopes=frozenset(["admin:system:configure", "admin:users:manage"])
)

with manager.bind(principal=principal, tenant_id="tenant1"):
    configure_system()
```

## See Also

- [SecurityContext](security_context.md)
- [Authorization](authz.md)
- [Error Types](security_errors.md)
