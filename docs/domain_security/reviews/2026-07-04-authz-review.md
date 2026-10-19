# Code Review: authz Feature

**Date:** 2026-07-04  
**Branch:** feat/v01-containers  
**Verdict:** CHANGES-REQUIRED

## Scope Reviewed

**Source files:**
- `domain_security/services/authz/authz_objects.py`
- `domain_security/services/authz/authz_client.py`
- `domain_security/services/authz/__init__.py`
- `domain_security/services/constants/authz.py`

**Test files:**
- `domain_security/services/tests/test_authz/` (conftest.py + test_authz_client.py + test_authz_objects.py)

**Coverage:** 100% (5 source files, 0 lines uncovered)

## Standards Dimensions Checked

All 17 core standards dimensions derived from STANDARDS.md and cohesive-cleanup.md were evaluated:

1. **Frozen+slots dataclasses** (no repr=False) - PASS: Permission and PolicyDecision use `@dataclass(frozen=True, slots=True)`.
2. **Facade ban** (no module-level domain functions) - PASS: Authorizer encodes all logic; no module-level domain functions.
3. **Objects/client split with as objs aliasing** - PASS: client imports objects as `authz_objects as objs`.
4. **Absolute imports everywhere** - PASS: All imports are absolute.
5. **__all__ + combined re-exports** - PASS: __init__.py declares __all__ with three public exports.
6. **One-line docstrings on every module/class/method** - PASS: Every module, class, and method has a one-line docstring.
7. **No inline comments** - PASS: No inline # comments present.
8. **Intuitive names + no single-letter TypeVars** - PASS: No generic types used; names are self-documenting.
9. **Signature stacking (3+ params after self/cls)** - N/A: No methods exceed 2 params after self/cls.
10. **Constants modules with Final + docstring dividers** - WARN: REASON_NO_PRINCIPAL and REASON_MISSING_SCOPE are semantic error messages but named with REASON_ prefix instead of ERR_ (authz.py:9-10). Inconsistent with tenancy.py and secrets.py which use ERR_ prefix (e.g., ERR_TENANCY_NO_TENANT_BOUND, ERR_SECRETS_NO_BACKEND).
11. **Error messages via const.ERR_*** - WARN: authz.py uses REASON_ prefix for error message constants (authz.py:9-10) instead of ERR_ pattern. Used in authz_client.py:35 when raising AuthzError and passed to PolicyDecision.reason at line 23 and 26.
12. **Test<Concern> classes + fixtures-in-conftest + 100% coverage** - PASS: TestAuthorizer class in test file; fixtures defined in conftest.py; 100% coverage achieved.
13. **Field-grouping by concern** - N/A: Permission and PolicyDecision are simple DTOs.
14. **Module docstrings general-to-file** - PASS: One-line docstrings on all source files.
15. **Error wrapping with @wrap_errors or manual wrap/raise from e** - PASS: authz_client.py:35 raises AuthzError directly without try-catch wrapping (appropriate for policy evaluation logic).
16. **No AI attribution, brand-generic, no em dashes** - PASS: No attribution trailers, no brand literals, no em dashes.
17. **Collections.abc over typing.ABCs** - PASS: No abstract base classes imported from typing.

## Findings

**WARNING (naming consistency):** Constants in `domain_security/services/constants/authz.py` use REASON_ prefix instead of ERR_ prefix for error message strings.

- **File:Line:** authz.py:9-10
  - `REASON_NO_PRINCIPAL = "no authenticated principal"`
  - `REASON_MISSING_SCOPE = "missing scope {scope}"`
  
  **Issue:** Error message constants used by AuthzError (authz_client.py:35, 26, 23) should follow the ERR_* naming convention for consistency with tenancy.py (ERR_TENANCY_NO_TENANT_BOUND, ERR_TENANCY_BOUNDARY_VIOLATION) and secrets.py (ERR_SECRETS_NO_BACKEND). The test file (test_authz_client.py:26, 38-40) already references these as decision reasons, but the pattern divergence creates maintenance friction.

  **Recommendation:** Rename:
  - REASON_NO_PRINCIPAL -> ERR_AUTHZ_NO_PRINCIPAL
  - REASON_MISSING_SCOPE -> ERR_AUTHZ_MISSING_SCOPE
  
  Update all references in authz_client.py and test files accordingly.

## OBA Compliance Attestation

This feature uses only public patterns (dataclasses, typing, standard library exception handling). No proprietary IP references, no internal project-management language, no AI-attribution trailers. Code follows generic authorization patterns.

## Verdict

**CHANGES-REQUIRED**

Address the ERR_* naming consistency issue before merge.

---

**Resolution (2026-07-04):** finding applied; constants renamed to `ERR_AUTHZ_NO_PRINCIPAL` and `ERR_AUTHZ_MISSING_SCOPE` across constants module, client, tests, and docs. Verdict updated: SHIP.
