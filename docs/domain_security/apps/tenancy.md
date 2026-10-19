# Tenant Isolation with TenancyGuard and @tenant_scoped

## Purpose

TenancyGuard enforces tenant boundaries, ensuring that operations stay within the tenant boundary by comparing the ambient SecurityContext's tenant_id against the tenant_id of the operation being performed. Multi-tenant services use this to prevent cross-tenant data access.

The @tenant_scoped decorator applies tenant checks declaratively to service methods, reading the ambient SecurityContext and enforcing that the context's tenant_id matches the operation's tenant_id before the method runs.

## Behavior

TenancyGuard.check() raises TenancyError if:
- The ambient context has no tenant_id bound.
- The ambient context's tenant_id differs from the target tenant_id.

The @tenant_scoped decorator extracts the tenant_id from a named function argument or from an instance attribute (self.tenant_id) and calls the guard's check() method.

## Public Surface

### @tenant_scoped Decorator

The decorator is applied at the module level and takes a parameter name:

```python
from domain_security import tenant_scoped

# Bind to a named function argument
@tenant_scoped("tenant_id")
def delete_document(doc_id: str, tenant_id: str) -> None:
    pass

# Bind to an instance attribute
@tenant_scoped("self.tenant_id")
def list_documents(self) -> list:
    pass
```

The decorator enforces that the ambient SecurityContext's tenant_id matches the extracted tenant_id before the decorated method runs. Mismatch raises TenancyError.

## Constants

- `SELF_TENANT_ID = "self.tenant_id"` (sentinel value to extract tenant_id from instance attribute)
- `ERR_TENANT_SCOPED_UNBOUND_SELF = "self.tenant_id requires a bound method call"` (raised when @tenant_scoped("self.tenant_id") is used on an unbound function)
- `ERR_TENANT_SCOPED_PARAM_MISSING = "tenant parameter missing from call"` (raised when the named parameter is not in the call)

See `domain_security/decorators/constants/tenant_scoped.py`.

## Error Semantics

@tenant_scoped raises TenancyError if:
- The ambient context has no tenant_id bound.
- The ambient context's tenant_id does not match the extracted tenant_id.
- The parameter cannot be extracted (unbound self, missing parameter).

See [Error Types](security_errors.md) for TenancyError details.

## Example Usage

### Tenant-scoped with a function argument

```python
from domain_security import tenant_scoped, TenancyError, Principal, SecurityContextManager

@tenant_scoped("tenant_id")
def delete_document(doc_id: str, tenant_id: str) -> None:
    print(f"Deleted {doc_id} from tenant {tenant_id}")

# Successful call: context matches argument
manager = SecurityContextManager()
with manager.bind(principal=Principal(id="user1"), tenant_id="acme"):
    delete_document("doc1", "acme")

# Failed call: context does not match
with manager.bind(principal=Principal(id="user1"), tenant_id="acme"):
    try:
        delete_document("doc2", "other")
    except TenancyError as e:
        print(f"Tenant violation: {e.message}")
```

### Tenant-scoped with self.tenant_id

```python
from domain_security import tenant_scoped, Principal, SecurityContextManager

class DocumentService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    @tenant_scoped("self.tenant_id")
    def list_documents(self) -> list:
        return ["doc1", "doc2"]

# Successful call: context matches self.tenant_id
manager = SecurityContextManager()
with manager.bind(principal=Principal(id="user1"), tenant_id="acme"):
    service = DocumentService("acme")
    docs = service.list_documents()
    print(f"Documents: {docs}")

# Failed call: context does not match self.tenant_id
with manager.bind(principal=Principal(id="user1"), tenant_id="acme"):
    try:
        service = DocumentService("other")
        service.list_documents()
    except TenancyError as e:
        print(f"Tenant violation: {e.message}")
```

### Multi-argument method with tenant_id

```python
from domain_security import tenant_scoped, Principal, SecurityContextManager

@tenant_scoped("tenant_id")
def update_document(doc_id: str, title: str, tenant_id: str, author: str = "unknown") -> dict:
    return {"id": doc_id, "title": title, "author": author, "tenant": tenant_id}

manager = SecurityContextManager()
with manager.bind(principal=Principal(id="user1"), tenant_id="acme"):
    result = update_document("doc1", "New Title", "acme", author="Alice")
    print(result)
```

## See Also

- [SecurityContext](security_context.md)
- [Error Types](security_errors.md)
