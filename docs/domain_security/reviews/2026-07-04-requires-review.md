# Code Review: requires Feature

**Date:** 2026-07-04  
**Branch:** feat/v01-containers  
**Verdict:** SHIP

## Scope Reviewed

**Source files:**
- `domain_security/decorators/requires/requires_client.py`
- `domain_security/decorators/requires/__init__.py`

**Test files:**
- `domain_security/decorators/tests/test_requires/` (conftest.py + test_requires_client.py)

**Coverage:** 100% (2 source files, 0 lines uncovered)

## Standards Dimensions Checked

All 17 core standards dimensions derived from STANDARDS.md and cohesive-cleanup.md were evaluated:

1. **Frozen+slots dataclasses** (no repr=False) - N/A: Feature uses no dataclasses (Requires is a decorator factory callable class).
2. **Facade ban** (no module-level domain functions) - PASS: Requires encodes decorator logic; module-level `requires = Requires()` instance is a sanctioned idiom (like tenant_scoped module-level instance in tenant_scoped).
3. **Objects/client split with as objs aliasing** - N/A: Feature imports from authz (Permission, Authorizer) and context (SecurityContextManager, SecurityContext) using proper absolute imports.
4. **Absolute imports everywhere** - PASS: All imports are absolute.
5. **__all__ + combined re-exports** - PASS: __init__.py declares __all__ with two public exports (Requires, requires).
6. **One-line docstrings on every module/class/method** - PASS: Every module, class, and method has a one-line docstring.
7. **No inline comments** - PASS: No inline # comments present.
8. **Intuitive names + no single-letter TypeVars** - PASS: Uses Params = ParamSpec("Params") and Return = TypeVar("Return") following the suite convention (not single-letter F/T/P/R).
9. **Signature stacking (3+ params after self/cls)** - N/A: No methods exceed 2 params after self/cls.
10. **Constants modules with Final + docstring dividers** - N/A: Feature has no constants module (uses from authz and tenant_scoped).
11. **Error messages via const.ERR_*** - N/A: Errors raised by authz feature (AuthzError), not requires.
12. **Test<Concern> classes + fixtures-in-conftest + 100% coverage** - PASS: TestRequires class in test file; fixtures in conftest.py; 100% coverage achieved.
13. **Field-grouping by concern** - N/A: No value objects defined in feature.
14. **Module docstrings general-to-file** - PASS: One-line docstring on requires_client.py.
15. **Error wrapping with @wrap_errors or manual wrap/raise from e** - PASS: requires_client.py:38 delegates to authorizer.require() which raises AuthzError; no try-catch wrapping (appropriate for decorator pattern).
16. **No AI attribution, brand-generic, no em dashes** - PASS: No attribution trailers, no brand literals, no em dashes.
17. **Collections.abc over typing.ABCs** - PASS: Imports Callable from collections.abc (line 6), not typing.

## Findings

None. All standards dimensions conform. Decorator pattern with functools.wraps and ParamSpec/TypeVar generics is correctly implemented.

## OBA Compliance Attestation

This feature uses only public patterns (functools, collections.abc, typing, standard library). Decorator composition follows generic Python best practices. No proprietary IP references, no internal project-management language, no AI-attribution trailers.

## Verdict

**SHIP**
