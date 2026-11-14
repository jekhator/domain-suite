# domain-errors optimization pass (2026-10-19)

## Purpose

This optimization pass reviews every Python module and test module of the
domain_errors package against correctness, dead and duplicated code, control
flow, typing, constants, naming, formatting, performance and test quality. Each
file was read in full. Findings that change observable behaviour are listed in
the Behavior changes section and in the changelog; anything else is a code
hygiene change. Public names, message constants, classifier families and the
exported surface of the package are unchanged.

Scope: 53 Python files under domain_errors/ at the base commit (30 source and
23 test files). Two constants modules were added and one placeholder module was
removed, so the per-file table has 55 rows: 53 base rows plus the two added
files. Gate results are recorded at the end of this document.

## Behavior changes

1. `@wrap_errors` on a call whose arguments do not match the function signature.
   Previously the argument-capture step raised a bind-time `TypeError` that
   escaped the wrapper, so the caller never received the target `DomainError`.
   Now the wrapper raises the target `DomainError` from the original `TypeError`
   with an empty context. Covered by a new test in the wrap_errors test module.
2. The empty module `domain_errors.services.constants.services` was removed. It
   held only a docstring, was not imported by the package or its tests, and was
   not part of the exported surface.

## Changes

- The `@wrap_errors` marker attribute name and the target-type message moved to
  a decorator constants module, referenced through the `const` alias. The
  message text is unchanged.
- Argument-capture helpers are typed with `object` and `Mapping` instead of `Any`
  and `dict`.
- Test assertions that wrapped a raise in try/except blocks (which pass silently
  when nothing is raised) now use `pytest.raises`.
- Test assertions for the target-type message and the default domain use their
  constants instead of literals.
- Single-letter local names in the chain objects tests were renamed.
- Non-ASCII characters in one test docstring were replaced with ASCII.
- Docstrings that referenced internal project terms were reworded.

## Per-file review

| path | findings | changed | note |
| --- | --- | --- | --- |
| domain_errors/decorators/constants/__init__.py | new module docstring | yes (added) | constants package for the decorator concern |
| domain_errors/decorators/constants/wrap_errors.py | new constants module for the marker and the target-type message | yes (added) | imported as const |
| domain_errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/common/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/common/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/common/constants/tests.py | 1: shared test-constants module has no importer | no | kept; removal would also change the wheel exclude list, deferred |
| domain_errors/common/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/config/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/config/_version.py | none | no | version bump belongs to the release step |
| domain_errors/decorators/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/decorators/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/decorators/tests/test_wrap_errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/decorators/tests/test_wrap_errors/conftest.py | 1: fixture module holds no fixtures | no | docstring-only conftest kept as the per-package fixture home |
| domain_errors/decorators/tests/test_wrap_errors/test_wrap_errors_client.py | 4: silent try/except assertions; literal match string; no test for unbindable calls; one weak dataclass check kept as is | yes | silent assertions converted to pytest.raises; match uses the constant; new test for the unbindable-call fallback |
| domain_errors/decorators/wrap_errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/decorators/wrap_errors/wrap_errors_client.py | 4: bind-time TypeError escapes on mismatched calls (fixed); marker and message literals inline (moved to constants); Any in helper signatures (typed); per-error signature introspection (candidate, deferred) | yes | fallback to empty context on bind failure; constants referenced through the const alias; signature cached-at-decoration is a design change, deferred |
| domain_errors/domains/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/cloud/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/cloud/cloud_client.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/constants/cloud.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/constants/domain_error.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/constants/http.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/constants/python.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/domain_error/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/domain_error/domain_error.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/http/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/http/http_client.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/python/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/python/python_client.py | none; family ordering checked (subclass entries precede OSError) | no | no change |
| domain_errors/domains/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_cloud/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_cloud/conftest.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_cloud/test_cloud_client.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_domain_error/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_domain_error/conftest.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_domain_error/test_domain_error.py | 2: internal project wording in two docstrings; silent try/except assertion | yes | wording replaced; assertion uses pytest.raises |
| domain_errors/domains/tests/test_http/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_http/conftest.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_http/test_http_client.py | 1: non-ASCII arrow characters in docstrings | yes | replaced with plain punctuation; per-test library imports kept so each test names its library |
| domain_errors/domains/tests/test_python/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_python/conftest.py | none | no | reviewed against every lens; no finding |
| domain_errors/domains/tests/test_python/test_python_client.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/chain/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/chain/chain_client.py | 2: history() reuses the error's context mapping, so link context aliases error context (candidate, deferred); wrap() accepts err without using it | no | public signature kept; aliasing change is a behaviour decision, deferred |
| domain_errors/services/chain/chain_objects.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/constants/chain.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/constants/services.py | 1: empty placeholder never imported | yes (removed) | removed; listed under Removed in the changelog |
| domain_errors/services/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/tests/test_chain/__init__.py | none | no | reviewed against every lens; no finding |
| domain_errors/services/tests/test_chain/conftest.py | none; fake classifier lives in the conftest and is imported by test modules | no | kept |
| domain_errors/services/tests/test_chain/test_chain_client.py | 2: silent try/except assertion; literal default domain in assertions | yes | pytest.raises used; assertions use the chain constant |
| domain_errors/services/tests/test_chain/test_chain_objects.py | 2: single-letter local names | yes | renamed to descriptive names |

## Deferred candidates

These were recorded during review and deliberately not changed in this pass,
because each one alters a design or a documented behaviour and needs its own
decision:

- `ErrorChain.history` places the error's own `context` mapping on each link,
  so a link's context aliases the error's context (`chain_client.py`).
- `ErrorChain.wrap` accepts `err` without using it; the parameter is kept for
  the public signature (`chain_client.py`).
- `WrapErrorsClient` recomputes `inspect.signature` on every raised error. Caching
  the signature at decoration time would be faster but changes the client shape
  (`wrap_errors_client.py`).
- `domain_errors.common.constants.tests` has no importer; removing it would also
  change the wheel exclusion list (`common/constants/tests.py`).

## Gate results

Commands were run from the worktree of the pass branch.

- `uv run --python 3.12 pytest -v --cov --cov-fail-under=100`: 732 passed,
  coverage 100.00 percent.
- `uv run --python 3.14 pytest -v --cov --cov-fail-under=100`: 732 passed,
  coverage 100.00 percent.
- Base before this pass: 729 passed, coverage 100.00 percent. Within this root,
  the test count rose from 188 to 189.
- `uv run mypy domain_aspects/ domain_rag/`: no issues in 61 source files.
- `uvx ruff@0.15.14 check .`: all checks passed.
- `uvx ruff@0.15.14 format --check . --exclude test_version_consistency.py`: 244
  files already formatted.
- `strict-module` at strict-suite 0.4.0 over the six package roots: exit 0 for
  each root.
- `strict-module loc-cap` over the six package roots: within the 300 LOC cap.
- Markdown dash grep: no matches.
- Attribution grep over the commits of this pass: no matches.

## Repository-level closing

The optimization pass covers six per-root documents, one for each import root,
and this repository-level section. Each per-root document has its own per-file
review table, behavior changes, deferred candidates and gate results.

- [domain_errors](2026-10-19-optimization-pass.md) (this document)
- [domain_security](../../domain_security/audits/2026-10-19-optimization-pass.md)
- [domain_api_limiter](../../domain_api_limiter/audits/2026-10-19-optimization-pass.md)
- [domain_aspects](../../domain_aspects/audits/2026-10-19-optimization-pass.md)
- [domain_monitoring](../../domain_monitoring/audits/2026-10-19-optimization-pass.md)
- [domain_rag](../../domain_rag/audits/2026-10-19-optimization-pass.md)

Repository-root files reviewed in the last leg:

| path | findings | changed | note |
| --- | --- | --- | --- |
| conftest.py | 1: autouse fixtures had no remaining users once the version test moved | yes (removed) | removed after a run without it passed |
| test_version_consistency.py | 2: hard-coded version literal; module-level imports moved into the test body | yes (moved) | moved to domain_errors/tests/test_version_consistency.py; compares every root with the distribution version |

Whole-suite gate results at the end of the pass:

- `uv run --python 3.12 pytest -v --cov --cov-fail-under=100`: 756 passed;
  coverage 100.00 percent. Base before the last leg: 738 passed.
- `uv run --python 3.14 pytest -v --cov --cov-fail-under=100`: 756 passed;
  coverage 100.00 percent.
- `uv run mypy domain_aspects/ domain_rag/`: Success: no issues found in 63
  source files.
- `uvx ruff@0.15.14 check .`: All checks passed!
- `uvx ruff@0.15.14 format --check .`: 248 files already formatted, with no
  exclude.
- `strict-module` at strict-suite 0.4.0 over the six roots: exit 0 for each root.
- `strict-module loc-cap` over the six roots: within the 300 LOC cap.
- `uv lock --check`: exit 0.
- Markdown dash grep and markdown hygiene greps: no matches.
- Attribution grep over the commits of the pass: no matches.
