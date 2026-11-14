# Security Audit: requires

**Audited**: 2026-07-04  
**Feature**: Declarative permission enforcement decorator  
**Scope**: Requires decorator factory; permission precondition; context binding

## Input Handling and Validation Surface

### Requires Class

**Requires.__init__** (domain_security/decorators/requires/requires_client.py:25-27):
- Accepts optional `authorizer: Authorizer | None`.
- Defaults to `Authorizer()` if None (line 27).
- Stores authorizer instance; no validation.

### Decorator Factory

**__call__** (line 29-45):
- Input: `permission: str` (permission name to enforce).
- Returns a decorator function.
- No validation of permission string; caller provides permission name.

**Decorated Function Wrapper** (line 36-41):
- Signature: `wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return`.
- Step 1 (line 38-40): Call `self._authorizer.require(self._current_context(), Permission(permission))`.
  - _current_context() returns ambient SecurityContext or anonymous context (line 48-51).
  - Permission is constructed with permission string (line 40).
  - Authorizer.require() raises AuthzError if denied (see authz audit).
- Step 2 (line 41): Only if authorization passes, call original function.

**Precondition Enforcement**: Authorization is enforced BEFORE wrapped function executes. If Authorizer.require() raises, the wrapped function never runs.

### Context Extraction

**_current_context()** (line 47-51):
- Calls SecurityContextManager().get() to retrieve ambient ContextVar value.
- If None, constructs anonymous SecurityContext(principal=None, tenant_id=None).
- Anonymous context fails authz checks (see authz audit: no principal -> deny).
- No ambient defaults; unset context is treated as unauthenticated.

## Secret Hygiene

**No secrets handled in decorator flow.** Permission string and context principal/tenant are identifiers only, not credentials.

**No Logging**: Decorator does not log the wrapped function's arguments or return value. If wrapped function logs secrets, that is caller's responsibility.

**Error Propagation**: If wrapped function raises with secret in its message, that error is not modified by the decorator; it propagates as-is. (Security.md accuracy note: this is caller-side secret-handling risk, not decorator-specific.)

## Deny-by-Default Posture

**Authorization Before Execution**:
1. Ambient context retrieved or defaulted to anonymous (no principal).
2. Authorizer.require() called (raises if denied).
3. Wrapped function only executes if authorization passes.

**No Implicit Allow**: Missing permission -> deny. No default allow, no permission inheritance, no role-based elevation.

**Anonymous Denies All**: Unset context produces anonymous SecurityContext with principal=None, which fails the first authz gate (no principal -> deny).

## Error-Content Review

**Authorization Errors**:
- If Authorizer.require() raises AuthzError (see authz audit), the exception propagates to caller.
- AuthzError contains permission name and deny reason (safe metadata).
- Original wrapped function does not execute; no partial-execution state leak.

**Function Errors**:
- If wrapped function raises, decorator does not catch or modify the error.
- Function's own exception (with any secrets it may log) propagates as-is to caller.

## Dependency Surface

- **stdlib**: functools, typing, collections.abc.
- **domain_security internals**: SecurityContextManager, SecurityContext, Authorizer, Permission.
- **Single decorator instance**: Module exports `requires = Requires()` (line 54), providing standard usage.

## Verdict

**PASS**

Precondition enforcement (authorization before execution), deny-by-default ambient context (anonymous on unset), immutable Permission and SecurityContext, and safe error propagation form a sound decorator surface. No secret handling risk; wrapped function execution is guarded by authorization check.
