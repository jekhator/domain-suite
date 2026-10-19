# domain-api-limiter optimization pass (2026-10-19)

## Purpose

This optimization pass reviews every Python module and test module of the
domain_api_limiter package against correctness, dead and duplicated code, control
flow, typing, constants, naming, formatting, performance and test quality. Each
file was read. Findings that change observable behaviour are listed in the
Behavior changes section and in the changelog; anything else is a code hygiene
change. Public names, rule messages, the decorator and registry surface, and
the error hierarchy are unchanged.

Scope: 29 Python files under domain_api_limiter/ (16 source and 13 test files
at the base commit). Gate results are recorded at the end of this document.

## Behavior changes

1. Rate strings whose request count is a digit that Python accepts for
   `str.isdigit` but not for `int()` (for example a superscript digit) are now
   rejected as a `ThrottleDeclarationError` with the rate-format message.
   Previously the raw `ValueError` from `int()` escaped. Non-ASCII decimal
   digits that `int()` accepts are still parsed. Covered by two new tests.

## Changes

- Request counts are validated with `str.isdecimal`, which matches the set of
  characters `int()` accepts.
- The policy collection list and the public-method selection list carry
  concrete element types; the selection signature no longer uses `Any`.
- The decorator's declaration closure drops an `else` after a return.
- The services constants package gained a module docstring.
- A policy test that asserted only a lower bound on the collected count now
  asserts the exact count and the ordered scopes.

## Per-file review

| path | findings | changed | note |
| --- | --- | --- | --- |
| domain_api_limiter/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/config/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/config/_version.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/decorators/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/decorators/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/decorators/tests/test_throttled/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/decorators/tests/test_throttled/conftest.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/decorators/tests/test_throttled/test_throttled_client.py | 2: one unnecessary type-ignore on a getattr line; bare dict annotation in a fixture-style helper | no | cosmetic; deferred to a later test-tree pass |
| domain_api_limiter/decorators/throttled/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/decorators/throttled/throttled_client.py | 3: Any in public-method selection signature; untyped accumulator; redundant else after return | yes | concrete Callable element type; guard-style declare closure |
| domain_api_limiter/errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/api_limiter_errors.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/constants/api_limiter_errors.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/tests/test_api_limiter_errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/tests/test_api_limiter_errors/conftest.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/errors/tests/test_api_limiter_errors/test_api_limiter_errors.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/services/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/services/constants/__init__.py | 1: package without a module docstring | yes | one-line docstring added |
| domain_api_limiter/services/constants/policy.py | none; constants reviewed, each reaches a raise site or the period mapping | no | no change |
| domain_api_limiter/services/policy/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/services/policy/policy_client.py | 2: untyped accumulator; collect() would count an alias twice if a member is bound under two names (candidate, deferred) | yes | accumulator typed; alias de-duplication is a behaviour change, deferred |
| domain_api_limiter/services/policy/policy_objects.py | 1: isdigit accepts superscript digits that int() rejects (fixed) | yes | isdecimal check; behaviour change listed in the report and changelog |
| domain_api_limiter/services/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/services/tests/test_policy/__init__.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/services/tests/test_policy/conftest.py | none | no | reviewed against every lens; no finding |
| domain_api_limiter/services/tests/test_policy/test_policy_client.py | 1: class-level staticmethod test asserted only a lower bound | yes | exact count and ordered scopes asserted |
| domain_api_limiter/services/tests/test_policy/test_policy_objects.py | 1: no coverage of the digit-class boundary | yes | tests for superscript and non-ASCII decimal digits |

## Deferred candidates

These were recorded during review and deliberately not changed in this pass:

- `PolicyRegistry.collect` reports a policy twice when a single declared
  function is bound under two names in the same container (`policy_client.py`).
  Removing duplicates changes the collection contract.
- `Throttled._select_public_methods` documents that it skips descriptors; the
  filter is `callable` and does not name descriptors explicitly
  (`throttled_client.py`). The docstring is accurate for the members it returns.
- One test line carries a type-ignore comment that the checker does not need
  (`test_throttled_client.py`); it is cosmetic and left for a later test-tree pass.

## Gate results

Commands were run from the worktree of the pass branch.

- `uv run --python 3.12 pytest -v --cov --cov-fail-under=100`: 732 passed,
  coverage 100.00 percent.
- `uv run --python 3.14 pytest -v --cov --cov-fail-under=100`: 732 passed,
  coverage 100.00 percent.
- Base before this pass: 729 passed. Within this root, the test count rose
  from 132 to 134.
- `uv run mypy domain_aspects/ domain_rag/`: no issues in 61 source files.
- `uvx ruff@0.15.14 check .`: all checks passed.
- `uvx ruff@0.15.14 format --check . --exclude test_version_consistency.py`: 244
  files already formatted.
- `strict-module` at strict-suite 0.4.0 over the six package roots: exit 0 for
  each root.
- `strict-module loc-cap` over the six package roots: within the 300 LOC cap.
- Markdown dash grep: no matches.
- Attribution grep over the commits of this pass: no matches.
