# domain-security Package Architecture

## Domain Boundaries

```
Security Aspect Layer
=================================================================================

+-----------------------------------------------------------------------------+
| SecurityContext Spine                                                       |
| +------------------------------------------------------------------------+ |
| | SecurityContext(principal: Principal|None, tenant_id: str|None)        | |
| | Principal(id: str, roles: frozenset[str], scopes: frozenset[str])     | |
| +------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------+
                            ^                           ^
                            |                           |
                    Set/Get/Bind                  Enforcement/Decorators
                            |                           |
        +-------------------+-------------------+-------+------------------+
        |                   |                   |       |                  |
        v                   v                   v       v                  v
+--------------+  +--------------+  +--------------+  +-----------------+ +--------------+
| context/     |  | services/    |  | services/    |  | decorators/     | | services/    |
| security_    |  | authz/       |  | tenancy/     |  | requires/       | | secrets/     |
| context/     |  |              |  |              |  | tenant_scoped/  | |              |
|              |  |              |  |              |  |                 | |              |
| Manager:     |  | Authorizer:  |  | TenancyGuard:|  | @requires()     | | SecretRef:   |
| set()        |  | check()      |  | check()      |  | @tenant_scoped()| | resolve()    |
| get()        |  | require()    |  |              |  |                 | |              |
| bind()       |  |              |  |              |  | Module handles: | | SecretsBack. |
| clear()      |  | Permission:  |  |              |  | requires        | | fetch()      |
|              |  | value: str   |  |              |  | tenant_scoped   | |              |
| SecurityCtx: |  |              |  |              |  |                 | | SecretValue: |
| principal    |  | PolicyDec:   |  |              |  |                 | | get()        |
| tenant_id    |  | allowed      |  |              |  |                 | | __repr__()   |
|              |  | reason       |  |              |  |                 | | (masked)|
+--------------+  +--------------+  +--------------+  +-----------------+ +--------------+
        |                 |                 |                 |                 |
        +-----------------+-----------------+-----------------+-----------------+
                                         |
                                         v
                        +----------------------------------+
                        | errors/security_errors.py        |
                        |                                  |
                        | SecurityError(DomainError)      |
                        | +- AuthzError                    |
                        | +- TenancyError                  |
                        | +- SecretError                   |
                        |                                  |
                        | [All subclass DomainError from   |
                        |  domain-errors sibling]          |
                        +----------------------------------+

Aspects deliberately out of scope:
  - Masking, field-level redaction -> sensitivity-mixin (sibling)
  - Rate-limiting, quota enforcement -> domain-api-limiter (future)
  - Logging of security events -> domain-errors + logging-mixin (parent layer)
```

## Implemented Surface

### context/security_context/
Files: `security_context_objects.py` (Principal, SecurityContext) + `security_context_client.py` (SecurityContextManager, alias `objs`)

- `SecurityContextManager`
  - `set(ctx: SecurityContext) -> Token[SecurityContext | None]`: store context, return token
  - `get() -> SecurityContext | None`: retrieve current context
  - `bind(*, principal=None, tenant_id=None) -> AbstractContextManager[None]`: temporarily bind
  - `clear(token: Token[SecurityContext | None]) -> None`: clear by token
  - `_bound(ctx: SecurityContext) -> AbstractContextManager[None]`: private contextmanager for bind() internals; fresh-bind semantics

- `Principal` (frozen dataclass)
  - `id: str`: principal identifier
  - `roles: frozenset[str] = frozenset()`: role membership
  - `scopes: frozenset[str] = frozenset()`: delegated scopes

- `SecurityContext` (frozen dataclass)
  - `principal: Principal | None`: authenticated principal (None = anonymous)
  - `tenant_id: str | None`: tenant isolation boundary

### services/authz/
Files: `authz_objects.py` (Permission, PolicyDecision) + `authz_client.py` (Authorizer)

- `Authorizer`
  - `check(ctx: SecurityContext, permission: Permission) -> PolicyDecision`: evaluate decision
  - `require(ctx: SecurityContext, permission: Permission) -> None`: enforce, raise if denied

- `Permission` (frozen dataclass)
  - `value: str`: permission identifier

- `PolicyDecision` (frozen dataclass)
  - `allowed: bool`: allow/deny
  - `reason: str | None = None`: optional rationale

### services/tenancy/
Files: `tenancy_client.py` (TenancyGuard, client-only pure-behavior feature)

- `TenancyGuard`
  - `check(ctx: SecurityContext, tenant_id: str) -> None`: enforce tenant match

### services/secrets/
Files: `secrets_objects.py` (SecretsBackend, SecretValue) + `secrets_client.py` (SecretRef)

- `SecretsBackend` (Protocol)
  - `fetch(name: str) -> str`: fetch secret by name

- `SecretRef`
  - `name: str`: instance attr, secret identifier
  - `__init__(name: str)`: initialize with secret name
  - `resolve(backend: SecretsBackend | None = None) -> SecretValue`: resolve at call-time, wrapped with @wrap_errors(SecretError, capture=False)

- `SecretValue` (frozen dataclass)
  - `_value: str`: internal secret storage
  - `get() -> str`: return actual secret
  - `__repr__() -> str`: masked: `<SecretValue ***>`

### decorators/requires/
Files: `requires_client.py` (Requires, client-only pure-behavior feature)

- `Requires`
  - `__init__(authorizer: Authorizer | None = None)`: optional authorizer
  - `__call__(permission: str) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]`: decorate method
  - `_current_context() -> SecurityContext`: instance method, read ambient context; anonymous fallback when unset
  - Module handle: `requires = Requires()`: ready to use as `@requires("admin:write")`

### decorators/tenant_scoped/
Files: `tenant_scoped_client.py` (TenantScoped, client-only pure-behavior feature)

- `TenantScoped`
  - `__init__(guard: TenancyGuard | None = None)`: optional guard
  - `__call__(param_name: str) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]`: decorate method (param_name = tenant-bearing parameter name or 'self.tenant_id')
  - `_tenant_argument(signature: inspect.Signature, param_name: str, args: tuple, kwargs: Mapping) -> str`: staticmethod, extract tenant_id from call args/kwargs; None values raise TenancyError
  - `_current_context() -> SecurityContext`: instance method, read ambient context; anonymous fallback when unset
  - Module handle: `tenant_scoped = TenantScoped()`: ready to use as `@tenant_scoped("tenant_id")`

### errors/security_errors.py
- `SecurityError(DomainError)`: base error, carries DomainError contract (domain="security", code="security_error", http_status 403 default, default_message)
- `AuthzError(SecurityError)`: policy violation (code="authz_denied", http_status 403)
- `TenancyError(SecurityError)`: tenant boundary violation (code="tenant_boundary_violation", http_status 403)
- `SecretError(SecurityError)`: secret access error (code="secret_access_failed", http_status 500 override, wraps backend failures with __cause__)

### Public API (domain_security/__init__.py)
Re-exports: `requires`, `tenant_scoped`, `SecurityContext`, `Principal`, `SecurityContextManager`, `Authorizer`, `Permission`, `PolicyDecision`, `SecretRef`, `SecretValue`, `SecurityError`, `AuthzError`, `TenancyError`, `SecretError`, `SecurityDeclarationError`, `__version__`

---

