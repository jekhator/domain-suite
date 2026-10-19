# @tenant_scoped Decorator

## Purpose

The @tenant_scoped decorator enforces tenant-boundary checks on service methods. It reads the ambient SecurityContext and verifies that the context's tenant_id matches the tenant_id of the operation before the decorated function runs.

## Behavior

The @tenant_scoped decorator:
1. Extracts the tenant_id from a named function argument or from self.tenant_id (instance attribute).
2. Reads the ambient SecurityContext via SecurityContextManager.
3. If no context is bound, treats it as anonymous with tenant_id=None.
4. Calls TenancyGuard.check() to verify the context's tenant_id matches the extracted tenant_id.
5. Raises TenancyError if the check fails.
6. Calls the decorated function only if the check succeeds.

## Public Surface

### @tenant_scoped decorator (module-level instance)

```python
from domain_security import tenant_scoped

# Bind to a named function argument
@tenant_scoped("tenant_id")
def delete_document(doc_id: str, tenant_id: str) -> None:
    pass

# Bind to self.tenant_id on an instance method
@tenant_scoped("self.tenant_id")
def list_documents(self) -> list:
    pass
```

The decorator parameter specifies the source of the tenant_id:
- A string like "tenant_id" extracts the value from the function argument with that name.
- The special string "self.tenant_id" extracts the value from the instance attribute self.tenant_id.

## Constants

- `SELF_TENANT_ID = "self.tenant_id"` (sentinel for self.tenant_id binding)
- `ERR_TENANT_SCOPED_UNBOUND_SELF = "self.tenant_id requires a bound method call"` (raised when self.tenant_id is used on an unbound function)
- `ERR_TENANT_SCOPED_PARAM_MISSING = "tenant parameter missing from call"` (raised when the named parameter is not present)
- `ERR_TENANT_SCOPED_NULL_TENANT = "tenant argument resolved to None"` (raised when the extracted tenant value is None)

See `domain_security/decorators/constants/tenant_scoped.py`.

## Error Semantics

The @tenant_scoped decorator raises TenancyError if:
- The ambient context has no tenant_id bound (None).
- The ambient context's tenant_id does not match the extracted tenant_id.
- The extraction fails (missing parameter or unbound self).
- The extracted tenant value is None.

See [Error Types](security_errors.md) for TenancyError details.

## Example Usage

### Argument-based tenant extraction

```python
from domain_security import tenant_scoped, TenancyError, Principal, SecurityContextManager

@tenant_scoped("tenant_id")
def delete_document(doc_id: str, tenant_id: str) -> None:
    print(f"Deleted document {doc_id} from tenant {tenant_id}")

manager = SecurityContextManager()
principal = Principal(id="user1")

# Success: context tenant_id matches argument
with manager.bind(principal=principal, tenant_id="acme"):
    delete_document("doc1", "acme")

# Failure: context tenant_id differs from argument
with manager.bind(principal=principal, tenant_id="acme"):
    try:
        delete_document("doc2", "other")
    except TenancyError as e:
        print(f"Boundary violation: {e.message}")
```

### Instance attribute binding

```python
from domain_security import tenant_scoped, Principal, SecurityContextManager

class DocumentService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    @tenant_scoped("self.tenant_id")
    def list_documents(self) -> list:
        return ["doc1", "doc2"]

manager = SecurityContextManager()
principal = Principal(id="user1")

# Success: context tenant_id matches self.tenant_id
with manager.bind(principal=principal, tenant_id="acme"):
    service = DocumentService("acme")
    docs = service.list_documents()
    print(f"Documents: {docs}")

# Failure: mismatch
with manager.bind(principal=principal, tenant_id="acme"):
    try:
        service = DocumentService("other")
        service.list_documents()
    except TenancyError as e:
        print(f"Tenant mismatch: {e.message}")
```

### Multiple arguments with tenant_id

```python
from domain_security import tenant_scoped, Principal, SecurityContextManager

@tenant_scoped("tenant_id")
def update_document(
    doc_id: str,
    title: str,
    tenant_id: str,
    author: str = "unknown",
    version: int = 1
) -> dict:
    return {
        "id": doc_id,
        "title": title,
        "author": author,
        "version": version,
        "tenant": tenant_id
    }

manager = SecurityContextManager()
principal = Principal(id="user1")

with manager.bind(principal=principal, tenant_id="acme"):
    result = update_document(
        "doc1",
        "New Title",
        "acme",
        author="Alice",
        version=2
    )
    print(f"Updated: {result}")
```

### Combining @requires and @tenant_scoped

```python
from domain_security import requires, tenant_scoped, Principal, SecurityContextManager

@requires("documents:write")
@tenant_scoped("tenant_id")
def update_document(doc_id: str, title: str, tenant_id: str) -> dict:
    return {"id": doc_id, "title": title}

manager = SecurityContextManager()
principal = Principal(
    id="user1",
    scopes=frozenset(["documents:write"])
)

# Both checks run: @tenant_scoped first (inner), @requires second (outer)
with manager.bind(principal=principal, tenant_id="acme"):
    result = update_document("doc1", "Updated", "acme")
    print(f"Result: {result}")
```

### Multi-tenant service factory

```python
from domain_security import tenant_scoped, Principal, SecurityContextManager

class DocumentServiceFactory:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    @tenant_scoped("self.tenant_id")
    def get_service(self) -> "DocumentService":
        return DocumentService(self.tenant_id)

class DocumentService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

manager = SecurityContextManager()
principal = Principal(id="user1")

with manager.bind(principal=principal, tenant_id="acme"):
    factory = DocumentServiceFactory("acme")
    service = factory.get_service()
    print(f"Service created for tenant: {service.tenant_id}")
```

## See Also

- [SecurityContext](security_context.md)
- [Tenant Isolation](tenancy.md)
- [Error Types](security_errors.md)
