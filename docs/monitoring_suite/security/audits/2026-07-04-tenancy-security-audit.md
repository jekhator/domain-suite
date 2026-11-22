# Security Audit: tenancy

**Audited**: 2026-07-04  
**Feature**: Tenant-boundary enforcement via ambient security context  
**Scope**: TenancyGuard policy; tenant_id matching and context binding

## Input Handling and Validation Surface

### TenancyGuard Policy Enforcement

**check() Method** (monitoring_suite/security/services/tenancy/tenancy_client.py:15-27):
- Input: `ctx: SecurityContext`, `tenant_id: str` (caller-provided tenant identifier).
- Step 1 (line 17-20): If ctx.tenant_id is None, raise TenancyError with ERR_TENANCY_NO_TENANT_BOUND. This denies all operations on an unbound context.
- Step 2 (line 22-27): If ctx.tenant_id != tenant_id (string equality check), raise TenancyError with ERR_TENANCY_BOUNDARY_VIOLATION and pass both tenant_id and context_tenant_id to error constructor.
- No pass-through condition: only exact match (ctx.tenant_id == tenant_id) avoids error.

**Boundary Enforcement**: String comparison is exact; case-sensitive; no fuzzy matching or inheritance.

### Input Types

- `ctx: SecurityContext` is a frozen dataclass (immutable).
- `tenant_id: str` is caller-provided; callers extract from URL, request object, or decorated function arguments.
- No coercion or transformation of tenant_id; compared as-is.

## Secret Hygiene

**No secrets in tenancy flow.** tenant_id is a string identifier (UUID, account ID, name), not a credential. Deny reasons contain both the provided tenant_id and context_tenant_id for debugging, but neither is a secret.

**Error Logging**: TenancyError passes tenant_id and context_tenant_id in error context. These are audit identifiers, not confidential.

## Deny-by-Default Posture

**Two Deny Gates**:
1. No tenant bound in context (ctx.tenant_id is None) -> raise TenancyError immediately.
2. Tenant ID mismatch (ctx.tenant_id != tenant_id) -> raise TenancyError immediately.

**No Implicit Fallback**: If context is unbound or mismatched, the operation fails. No silent allow or default tenant assumption.

## Error-Content Review

**TenancyError Construction**:
- Line 18-20: `TenancyError(message=const.ERR_TENANCY_NO_TENANT_BOUND, tenant_id=tenant_id)`.
  - message is constant string "no tenant bound in security context".
  - tenant_id is the provided identifier (safe metadata).
- Line 24-27: `TenancyError(message=const.ERR_TENANCY_BOUNDARY_VIOLATION, tenant_id=tenant_id, context_tenant_id=ctx.tenant_id)`.
  - message is constant string "tenant boundary violation".
  - tenant_id and context_tenant_id are both string identifiers (audit metadata).

**Error Safety**: No secret values, principal state, or request payloads leaked in error context.

## Dependency Surface

- **stdlib only**: No external imports except monitoring_suite.errors.
- **monitoring_suite.errors**: Single import (DomainError base class for TenancyError).
- **monitoring_suite.security internals**: SecurityContext (immutable), constants module (ERR_* strings).

## Verdict

**PASS**

Deny-by-default enforcement (two gates, no fallback), exact string matching, immutable SecurityContext, and safe error messaging form a sound tenant-boundary isolation surface. No permission inference; no cross-tenant data leakage risk.
