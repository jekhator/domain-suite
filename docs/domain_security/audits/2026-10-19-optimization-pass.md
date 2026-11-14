# domain-security optimization pass (2026-10-19)

## Purpose

This optimization pass reviews every Python module of the domain_security
package, including its test modules, against correctness, dead and duplicated
code, control flow, typing, constants, naming, formatting, performance and test
quality. Each file was read in full. Findings that change observable behaviour
are listed in the Behavior changes section and in the changelog; every other
change is code hygiene. Exported names, aspect-facing signatures, constant
values that tests and documentation match against, and the public surface are
unchanged except where listed.

Scope: 64 Python files under domain_security/ at the base commit (34 source and
30 test modules, counting package initialisers). One helper module was added,
so the per-file table has 65 rows, one for every Python file in the package
tree at the end of the pass.

## Behavior changes

1. `@tenant_scoped` on a call whose tenant argument, or instance `tenant_id`
   used with `self.tenant_id`, is None now raises `TenancyError` with the new
   message `ERR_TENANT_SCOPED_NULL_TENANT`. Previously the value was converted
   with `str()`, so a None argument was compared as the text "None". A context
   bound to a tenant whose identifier is that text admitted such a call.
2. `Requires(authorizer=...)` and `TenantScoped(guard=...)` keep the supplied
   object when it evaluates as falsy. Previously an `or` expression replaced
   it with the default, so a falsy custom object was silently ignored. Only
   `None` selects the default now.
3. `@tenant_scoped` reads the decorated callable's signature once, when the
   decorator is applied. A callable whose signature cannot be read now fails at
   decoration time rather than at its first call.
4. The unused constant `ERR_TENANT_SCOPED_MISSING_PARAM` was removed from the
   decorator constants module. Nothing referenced it.

## Changes

- The class-level walk shared by `@requires` and `@tenant_scoped` moved into one
  helper class in a new module. Both decorators call it.
- `@requires` builds its `Permission` once per decorated callable instead of on
  every call, and reads an anonymous context constant instead of building one.
- `@tenant_scoped` binds arguments against the signature captured at decoration
  time and no longer rebuilds the signature on each call.
- Both decorator classes keep one `SecurityContextManager` per instance rather
  than constructing one per call.
- Type annotations on the tenant argument helper use `Mapping` and `object`
  instead of `dict[str, Any]` and `tuple[Any, ...]`.
- Test modules: per-test imports moved to module level; unused fixtures and an
  unused guard class were removed; bare `list` and `dict` annotations in test
  helpers were parameterised; one misnamed test and one misnamed secrets test
  were renamed and made to exercise what their names state; a weak assertion
  on the context token was made exact; a regression test covers the falsy
  authorizer, the None tenant rejection and the declaration error hierarchy.

## Per-file review

| path | findings | changed | note |
| --- | --- | --- | --- |
| domain_security/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/config/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/config/_version.py | none | no | version bump belongs to the release step |
| domain_security/conftest.py | none | no | reset fixture is the package-level isolation point |
| domain_security/context/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/context/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/context/constants/security_context.py | none | no | section labels are the constants-module style used across the package |
| domain_security/context/security_context/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/context/security_context/security_context_client.py | none | no | reviewed against every lens; no finding |
| domain_security/context/security_context/security_context_objects.py | none | no | reviewed against every lens; no finding |
| domain_security/context/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/context/tests/test_security_context/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/context/tests/test_security_context/conftest.py | none | no | reviewed against every lens; no finding |
| domain_security/context/tests/test_security_context/test_security_context_client.py | 1: token assertion only checked for presence | yes | asserts the token type |
| domain_security/context/tests/test_security_context/test_security_context_objects.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/class_fanout.py | new helper for the class-level walk | added | shared by requires and tenant_scoped |
| domain_security/decorators/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/constants/tenant_scoped.py | 2: unused declaration constant; no message for a None tenant | yes | removed the unused constant; added the None tenant message |
| domain_security/decorators/requires/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/requires/requires_client.py | 4: permission rebuilt per call; context manager and anonymous context rebuilt per call; `or` default drops falsy authorizers; duplicated class walk | yes | permission built once; instance manager; constant anonymous context; `is None` default; shared walk |
| domain_security/decorators/tenant_scoped/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/tenant_scoped/tenant_scoped_client.py | 6: signature rebuilt per call; None tenant converted to text; `or` default drops falsy guards; per-call context objects; duplicated class walk; Any in helper signatures | yes | signature captured at decoration; None rejected; instance guard default; shared walk; Mapping and object typing |
| domain_security/decorators/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/tests/test_requires/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/tests/test_requires/conftest.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/tests/test_requires/test_requires_class_level.py | 3: fixture parameter unannotated; bare list and dict annotations; authorizer type not imported | yes | annotated; imports added |
| domain_security/decorators/tests/test_requires/test_requires_client.py | 2: fixture parameter unannotated; no test for a falsy custom authorizer | yes | annotated; regression test added |
| domain_security/decorators/tests/test_tenant_scoped/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/decorators/tests/test_tenant_scoped/conftest.py | 2: unused guard class and fixtures | yes | conftest reduced to its docstring |
| domain_security/decorators/tests/test_tenant_scoped/test_tenant_scoped_class_level.py | 1: bare list and dict annotations in test helpers | yes | parameterised |
| domain_security/decorators/tests/test_tenant_scoped/test_tenant_scoped_client.py | 3: guard imported inside a test; no test for a None tenant argument or instance attribute | yes | hoisted import; two tests added |
| domain_security/errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/errors/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/errors/constants/security_errors.py | 1: the tenancy boundary constant shares its name with a services constant that has different text | no | deferred; see Deferred candidates |
| domain_security/errors/security_errors.py | none | no | reviewed against every lens; no finding |
| domain_security/errors/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/errors/tests/test_security_errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/errors/tests/test_security_errors/conftest.py | 1: fixtures not used by any test | yes | conftest reduced to its docstring |
| domain_security/errors/tests/test_security_errors/test_security_errors.py | 1: no test class for the declaration error | yes | class added |
| domain_security/services/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/authz/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/authz/authz_client.py | none | no | reviewed against every lens; no finding |
| domain_security/services/authz/authz_objects.py | none | no | reviewed against every lens; no finding |
| domain_security/services/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/constants/authz.py | none | no | reviewed against every lens; no finding |
| domain_security/services/constants/secrets.py | none | no | reviewed against every lens; no finding |
| domain_security/services/constants/tenancy.py | 1: the tenancy boundary constant shares its name with an errors constant that has different text | no | deferred; see Deferred candidates |
| domain_security/services/secrets/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/secrets/secrets_client.py | none | no | reviewed against every lens; no finding |
| domain_security/services/secrets/secrets_objects.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tenancy/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tenancy/tenancy_client.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_authz/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_authz/conftest.py | 2: fixtures not used by any test | yes | unused fixtures removed |
| domain_security/services/tests/test_authz/test_authz_client.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_authz/test_authz_objects.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_secrets/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_secrets/conftest.py | 1: no fixture backend holds a punctuated secret name | yes | one entry added for the new test |
| domain_security/services/tests/test_secrets/test_secrets_client.py | 1: test named for special characters did not test them and duplicated another | yes | rewritten to resolve a punctuated name |
| domain_security/services/tests/test_secrets/test_secrets_objects.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_tenancy/__init__.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_tenancy/conftest.py | none | no | reviewed against every lens; no finding |
| domain_security/services/tests/test_tenancy/test_tenancy_client.py | 1: test name says multi-line for colon-delimited identifiers | yes | renamed and docstring corrected |

## Deferred candidates

These were recorded during review and deliberately not changed in this pass,
because each one alters a message or a design and needs its own decision:

- `ERR_TENANCY_BOUNDARY_VIOLATION` exists in two constants modules with different
  text ("tenant boundary violation" in the tenancy constants, "Tenant boundary
  violation." in the security error constants). Unifying them changes the text
  of one of the two messages (`services/constants/tenancy.py`,
  `errors/constants/security_errors.py`).

## Gate results

Commands were run from a checkout of the pass branch with the locked dependency set.

- `uv run pytest -v --cov --cov-fail-under=100` on Python 3.12 and 3.14: 738
  passed in each run, coverage 100.00 percent.
- Tests before and after, per root: domain_security 170 before and 177 after;
  domain_aspects 146 before and 145 after; whole suite 732 before and 738 after
  (the whole-suite figure also includes the other roots).
- `uv run mypy domain_aspects/ domain_rag/`: no issues in 63 source files.
- `uvx ruff@0.15.14 check .`: all checks passed.
- `uvx ruff@0.15.14 format --check . --exclude test_version_consistency.py`: 247
  files already formatted.
- `strict-module` at strict-suite 0.4.0 over the six package roots: exit 0 for
  each root.
- `strict-module loc-cap` over the six package roots: every root within the 300
  LOC cap.
- Markdown dash grep: no matches.
- Attribution grep over the commits of this pass: no matches.
