# Security Audit: authz

**Audited**: 2026-07-04  
**Feature**: Scope-based authorization policy evaluation  
**Scope**: Permission value object; Authorizer policy engine; deny-by-default enforcement

## Input Handling and Validation Surface

### Permission and PolicyDecision Value Objects

**Permission** (monitoring_suite/security/services/authz/authz_objects.py:8-12):
- Frozen dataclass with slots.
- Field: `value: str` (permission name).
- No validation; caller constructs with a permission string.
- Immutability ensures permission name cannot be mutated post-creation.

**PolicyDecision** (monitoring_suite/security/services/authz/authz_objects.py:15-20):
- Frozen dataclass with slots.
- Fields: `allowed: bool`, `reason: str | None`.
- Immutable; safe to return from check() without internal state risk.

### Authorizer Policy Evaluation

**check() Method** (monitoring_suite/security/services/authz/authz_client.py:16-29):
- Input: `ctx: SecurityContext`, `permission: Permission`.
- Step 1 (line 22-23): If ctx.principal is None, deny with reason "no authenticated principal".
- Step 2 (line 24-28): If permission.value not in ctx.principal.scopes, deny with formatted reason.
- Step 3 (line 29): Allow.

**Deny-by-Default Flow**: Unset principal -> deny. Missing scope -> deny. No default allow.

### require() Method

**require() Method** (monitoring_suite/security/services/authz/authz_client.py:31-38):
- Input: `ctx: SecurityContext`, `permission: Permission`.
- Calls check() (line 33).
- If not decision.allowed, raises AuthzError with the denial reason (line 34-38).
- Error is raised BEFORE method execution (enforcement precedes wrapped call).

**Precondition Enforcement**: Authorization decision is made inline; no lazy evaluation or context capture that could defer denial.

## Secret Hygiene

**No secrets in authorization flow.** Permission names and scope strings are identifiers, not credentials. ctx.principal.scopes contains permission name strings only, not secret values.

**Deny Reasons**: Formatted with permission name (const.ERR_AUTHZ_MISSING_SCOPE.format(scope=permission.value)). No sensitive data in reason strings.

## Deny-by-Default Posture

**Three Deny Gates**:
1. No principal (unauthenticated) -> deny.
2. Principal exists but missing required scope -> deny.
3. Only explicit scope membership allows.

**No Implicit Defaults**: Scopes must be explicitly present in ctx.principal.scopes. Absence is denial.

## Error-Content Review

**AuthzError Construction** (line 35-38):
- `message=decision.reason` (contains permission name only, no secret/sensitive data).
- `permission=permission.value` (permission name string).
- Error object preserves both but does not leak secret values or principal state.

**Error Safety**: All error fields are safe metadata (names, identifiers).

## Dependency Surface

- **stdlib only**: No external imports in authz_objects.py or authz_client.py except monitoring_suite.errors.DomainError parent.
- **monitoring_suite.errors**: Single import (DomainError base class for AuthzError).
- **monitoring_suite.security internals**: SecurityContext, Permission, PolicyDecision (all immutable frozen dataclasses).

## Verdict

**PASS**

Deny-by-default policy (all three gates), frozen value objects, explicit scope membership check, and safe error messaging form a sound authorization surface. No principal state leakage; no lazy evaluation.
