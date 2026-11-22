# Security Audit: tenant_scoped

**Audited**: 2026-07-04  
**Feature**: Declarative tenant-boundary enforcement decorator  
**Scope**: TenantScoped decorator factory; tenant_id extraction via inspect.signature; tenancy check

## Input Handling and Validation Surface

### TenantScoped Class

**TenantScoped.__init__** (monitoring_suite/security/decorators/tenant_scoped/tenant_scoped_client.py:27-29):
- Accepts optional `guard: TenancyGuard | None`.
- Defaults to `TenancyGuard()` if None.
- Stores guard instance; no validation.

### Decorator Factory

**__call__** (line 31-46):
- Input: `param_name: str` (name of the tenant_id parameter to extract and check).
- Special value: `const.SELF_TENANT_ID` ("self.tenant_id") extracts from instance attribute.
- Returns a decorator function.

**Decorated Function Wrapper** (line 38-44):
- Step 1 (line 40): Call `self._tenant_argument(func, param_name, args, kwargs)` to extract tenant_id.
- Step 2 (line 41): Call `self._guard.check(self._current_context(), tenant_id)` to enforce tenant boundary.
- Step 3 (line 42): Only if tenancy check passes, call original function.

**Precondition Enforcement**: Tenancy is checked BEFORE wrapped function executes. If TenancyGuard.check() raises, the wrapped function never runs.

### Tenant ID Extraction

**_tenant_argument()** (line 48-66):
- Input: `func: Callable[..., Any]`, `param_name: str`, `args: tuple[Any, ...]`, `kwargs: dict[str, Any]`.
- Step 1 (line 56-59): Special case for "self.tenant_id".
  - Check args is non-empty (line 57).
  - If empty, raise TenancyError(const.ERR_TENANT_SCOPED_UNBOUND_SELF) (line 58).
  - Extract from `args[0].tenant_id` (the instance object's tenant_id attribute).
  - Convert to string (line 59).
- Step 2 (line 60): Call `inspect.signature(func).bind(*args, **kwargs)` to create a BoundArguments object.
  - This maps positional and keyword arguments to function parameters by name.
  - Fails if call is invalid (mismatched args/kwargs).
- Step 3 (line 61-65): Check if param_name exists in bound.arguments.
  - If missing, raise TenancyError(const.ERR_TENANT_SCOPED_PARAM_MISSING, param_name=param_name).
- Step 4 (line 66): Extract value and convert to string.

**Input Validation via inspect.signature.bind()**: Binding fails if the call signature is invalid (positional/keyword mismatch), which would raise TypeError and propagate to caller. This validates the function call signature.

**Implicit Conversions**: Both "self.tenant_id" and param_value are converted to string via `str()` (line 59, 66). If tenant_id is None or an object, str() will convert it. Caller responsibility to pass string-like tenant_id.

### Context Extraction

**_current_context()** (line 68-72):
- Same as requires decorator: retrieves ambient SecurityContext or defaults to anonymous.
- Anonymous context fails tenancy checks (ctx.tenant_id=None).

## Secret Hygiene

**No secrets handled in decorator flow.** param_name, tenant_id, and context are identifiers only.

**No Logging**: Decorator does not log the extracted tenant_id or function arguments.

**Tenant ID as Audit Identifier**: tenant_id is treated as a string identifier (UUID, account name, etc.), not a secret. TenancyGuard error includes tenant_id for debugging.

## Deny-by-Default Posture

**Tenancy Before Execution**:
1. Tenant ID extracted from parameter or instance attribute.
2. Ambient context retrieved or defaulted to anonymous (tenant_id=None).
3. TenancyGuard.check() called (raises if unbound or mismatched).
4. Wrapped function only executes if tenancy passes.

**No Implicit Allow**: Unbound context -> deny. Mismatch -> deny. No default tenant assumption.

**Anonymous Denies All**: Unset context produces anonymous SecurityContext with tenant_id=None, which fails TenancyGuard.check() (no tenant bound -> deny).

## Error-Content Review

### Parameter Extraction Errors

- Line 58: If self.tenant_id case and args is empty, TenancyError with message "self.tenant_id requires a bound method call".
- Line 62-65: If param_name not in bound.arguments, TenancyError with message "tenant parameter missing from call" and param_name as metadata.

**Error Safety**: Error metadata contains parameter name (identifier), not the tenant_id value itself.

### Tenancy Boundary Errors

- Raised by TenancyGuard.check() (see tenancy audit).
- Includes tenant_id and context_tenant_id for debugging (audit metadata).

## Dependency Surface

- **stdlib**: functools, inspect, typing, collections.abc.
- **monitoring_suite.security internals**: SecurityContextManager, SecurityContext, TenancyGuard, constants (SELF_TENANT_ID, ERR_*).
- **Single decorator instance**: Module exports `tenant_scoped = TenantScoped()` (line 75).

## Inspection Surface Risk

**inspect.signature.bind()**: Does not execute user code; it parses the function signature and binds parameters by name. This is safe for sandboxed introspection.

**Edge Case**: If a function parameter is named "self.tenant_id" (dot in the parameter name, which is invalid Python syntax), the special case comparison (line 56) would not match. However, Python forbids dots in parameter names, so this is not a practical risk.

## Verdict

**PASS**

Precondition enforcement (tenancy before execution), deny-by-default ambient context (anonymous on unset), safe parameter extraction via inspect.signature.bind(), and explicit "self.tenant_id" handling form a sound decorator surface. No secret handling risk; inspection is read-only; wrapped function execution is guarded by tenancy check.
