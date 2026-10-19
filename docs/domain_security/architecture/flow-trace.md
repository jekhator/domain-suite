# domain_security: Flow-Trace

## Overview

Ambient security context management via contextvars, permission-based access control via `@requires`, and tenant isolation via `@tenant_scoped`. Principal identity and tenant boundaries are immutable frozen objects. Authorization is scope-based: principal holds frozenset[scopes], permission check matches against them.

## Entry Unit

`SecurityContext` [FROZEN,slots] (principal, tenant_id) + `SecurityContextManager` (contextvar binding) + `@requires(permission)` decorator.

## Flow-Trace Diagram

```
(1) CONSTRUCT SecurityContext
   class Principal [FROZEN,slots]
      id: str
      roles: frozenset[str] = frozenset()
      scopes: frozenset[str] = frozenset()

   class SecurityContext [FROZEN,slots]
      principal: Principal | None
      tenant_id: str | None

   SecurityContextManager._context: ContextVar[SecurityContext | None] = ContextVar("domain_security_context", default=None)

(2) BIND Context (contextvar set/reset)
   with SecurityContextManager().bind(principal=principal, tenant_id=tenant_id):
      +- objs.SecurityContext(principal=principal, tenant_id=tenant_id)  <- create fresh context
      +- _bound(ctx)  +- contextmanager decorator
      |  +- token = set(ctx)  <- store in ContextVar, save reset token
      |  +- try:  yield  <- execute with-block
      |  +- finally:  clear(token)  <- restore prior context
      +- return AbstractContextManager[None]

(3) DECORATE @requires
   @requires(permission="admin:read")  --> Requires(authorizer=Authorizer())
      +- __call__(permission="admin:read")  --> decorate(target)
      |  +- isclass(target)?  --> _decorate_class(target, permission)
      |  |  +- iterate target.__dict__, skip _-prefixed/properties/dunders/nested classes
      |  |     +- classmethod/staticmethod: unwrap, decorate, rewrap
      |  |     +- callable: _decorate_callable(method, permission)
      |  +- callable(target)  --> _decorate_callable(target, permission)
      |     +- @functools.wraps(func)
      |     +- def wrapper(*args, **kwargs):  setter = _REQUIRES_DECORATED_MARKER on wrapper
      |     +- setattr(wrapper, "__requires_decorated__", True)
      +- returns decorated callable or class

(4) RUNTIME Call --> wrapper(*args, **kwargs)
      +- _current_context()  <- SecurityContextManager().get() or SecurityContext(None, None)
      +- authorizer.require(ctx, Permission(permission="admin:read"))
      |  +- decision = check(ctx, permission)
      |  |  +- if ctx.principal is None  --> PolicyDecision(allowed=False, reason=ERR_AUTHZ_NO_PRINCIPAL)
      |  |  |  +- reason: "no authenticated principal"
      |  |  +- if permission.value not in ctx.principal.scopes
      |  |  |  +- reason=ERR_AUTHZ_MISSING_SCOPE.format(scope=permission.value)
      |  |  |     +- reason: "missing scope admin:read"
      |  |  +- else  --> PolicyDecision(allowed=True)
      |  +- if not decision.allowed  --> raise AuthzError(message=reason, permission=permission.value)
      +- return func(*args, **kwargs)  <- permission granted, execute

(5) RESULT (with permission)
   SUCCESS: {'id': '123', 'name': 'Alice'}

(6) RESULT (without permission, anonymous)
   CAUGHT AuthzError: AuthzError
     message: no authenticated principal
     permission: admin:read

REAL OUTPUT (permission granted):
   SUCCESS: {'id': '123', 'name': 'Alice'}

REAL OUTPUT (anonymous, denied):
   CAUGHT AuthzError: AuthzError
     message: no authenticated principal
     permission: admin:read
```

## Key Constants

- `CONTEXT_VAR_NAME` = "domain_security_context" (ContextVar name)
- `ERR_AUTHZ_NO_PRINCIPAL` = "no authenticated principal"
- `ERR_AUTHZ_MISSING_SCOPE` = "missing scope {scope}"
- `_REQUIRES_DECORATED_MARKER` = "__requires_decorated__"

## Core Classes

- `Principal` <- frozen slots; id, roles, scopes (each frozenset)
- `SecurityContext` <- frozen slots; principal, tenant_id
- `SecurityContextManager` <- _context: ContextVar; set(), get(), bind(), clear()
- `Requires` <- decorator factory; __init__(authorizer), __call__(permission), _decorate_callable, _decorate_class
- `Authorizer` <- check(ctx, permission) -> PolicyDecision; require(ctx, permission) raises AuthzError
- `Permission` <- frozen slots; value (str)
- `PolicyDecision` <- frozen slots; allowed (bool), reason (str)
- `AuthzError` <- DomainError subclass; message, permission (context)
