# domain-rag optimization pass (2026-10-19)

## Purpose

This optimization pass reviews every Python module and test module of the
domain_rag package against correctness, dead and duplicated code, control
flow, typing, constants, naming, formatting, performance and test quality.
Each file was read in full. Changes that alter observable behaviour are listed
under Behavior changes and in the 0.7.0 section of the changelog; the remaining
changes are code hygiene. Exported names, event fields, the message constants
and the public decorator signature are unchanged.

Scope: 33 Python files under domain_rag/ (21 source and 12 test files) at the
base commit, plus the package README and architecture page. Gate results are
recorded at the end of this document.

## Behavior changes

1. Tracing never changes the wrapped call's result. Previously a call with no
   arguments, or with an empty query, failed inside the provenance step and the
   result or original error was lost. The query is now recorded as the
   placeholder `(no query)` when no non-empty value is available.
2. Chunk and source ids are read only from list or tuple values. A value of any
   other type yields an empty tuple, and the result is returned unchanged.
   Previously the value was converted with `tuple()`, which failed on
   non-iterable values and consumed iterators.
3. A failing sink on a failed call adds a note to the call's exception and the
   original exception is raised. A failing sink on a successful call raises the
   sink error to the caller, so a missing provenance record is visible.
   Previously the failure was recorded a second time and the sink error replaced
   the result.
4. `@traced_retrieval` rejects an empty `principal_id` or `session_id` when it
   is applied, with `RetrievalDeclarationError`.
5. Class decoration wraps the public functions and method descriptors defined
   on the decorated class. An overridden method is now traced. A method
   inherited from a base class is not wrapped by the class decorator.
6. Classmethods and staticmethods on a traced class keep their descriptor type.
   Previously the wrapper was bound as an instance method.
7. A bound sink that evaluates as falsy is used. Only an unset sink selects the
   registry default.
8. Durations use `time.perf_counter()`.

## Changes

- The success and failure paths share helpers for the query, the id extraction,
  the provenance construction and the recording; the sync and async wrappers
  differ only in the await.
- The query placeholder, the note text, the query argument name and the result
  key names live in the provenance constants module; the declaration messages
  live in the retrieval constants module, referenced through the const alias.
- `ProvenanceRegistry` keeps one shared null sink instead of building one per
  lookup, and checks for an unset sink by identity.
- The package export list is sorted.
- Tests use `pytest.raises` with the constant messages, drop the try/except
  blocks that passed when nothing was raised, drop the no-op assertion, and
  cover the behaviours above.
- The package README and the retrieval flow-trace page describe the current
  API; their printed outputs are real runs at 0.7.0.

## Per-file review

| path | findings | changed | note |
| --- | --- | --- | --- |
| domain_rag/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/common/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/common/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/common/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/config/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/config/_version.py | none | yes | version bump to 0.7.0 |
| domain_rag/conftest.py | none | no | reviewed against every lens; no finding |
| domain_rag/decorators/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/decorators/traced_retrieval/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/decorators/traced_retrieval/traced_retrieval_client.py | 11: provenance validation inside the try could replace a successful result (zero-argument and empty-query calls, fixed); non-list id values could alter a result (fixed); success-path sink error recorded as a failed call (fixed); falsy sink selected by `or` (fixed); sync and async bodies duplicated (fixed); wall-clock durations (fixed); inherited base methods excluded by a first-base name check (fixed); classmethods and staticmethods rewrapped as instance methods (fixed); untyped public list and id tuples (typed); string keys in code (constants); no declaration check for principal_id and session_id (added) | yes | shared helpers; failure path keeps the exception; see Behavior changes |
| domain_rag/errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/errors/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/errors/constants/retrieval.py | 1: section labels as bare string expressions (converted to comments); declaration messages missing (added) | yes | constants added for the declaration checks |
| domain_rag/errors/retrieval_errors.py | none | no | reviewed against every lens; no finding |
| domain_rag/services/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/services/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/services/constants/provenance.py | none in the existing constants; placeholder, note text and key names added for the tracing wrapper | yes | new constants referenced through the const alias |
| domain_rag/services/provenance/__init__.py | 1: __all__ not sorted (sorted) | yes | export list unchanged apart from order |
| domain_rag/services/provenance/provenance_client.py | 1: redundant pass after the NullProvenanceSink docstring (removed) | yes | no behaviour change |
| domain_rag/services/provenance/provenance_objects.py | none | no | reviewed against every lens; no finding |
| domain_rag/services/registry/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/services/registry/registry_client.py | 2: falsy sink replaced by the null sink (fixed); NullProvenanceSink constructed on every lookup (shared instance) | yes | identity check; class-level fallback instance |
| domain_rag/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_provenance/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_provenance/conftest.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_provenance/test_provenance_client.py | 1: no-op assertion `assert True` (replaced with a check that the null sink keeps no state) | yes | assertion strengthened |
| domain_rag/tests/test_provenance/test_provenance_objects.py | 3: immutability test passed even when no exception was raised (pytest.raises); five validation tests wrapped the raise in try/except (pytest.raises, parametrized); messages written as literals (constants) | yes | parametrized validation test uses the constants |
| domain_rag/tests/test_registry/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_registry/conftest.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_registry/test_registry_client.py | 1: no test for a falsy bound sink (added) | yes | new test |
| domain_rag/tests/test_traced_retrieval/__init__.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_traced_retrieval/conftest.py | none | no | reviewed against every lens; no finding |
| domain_rag/tests/test_traced_retrieval/test_traced_retrieval_client.py | 1: result preservation, declaration checks, sink failures, classmethod binding and own-method fan-out had no tests (added in one test class) | yes | new test class |

## Deferred candidates

These were recorded during review and deliberately not changed in this pass,
because each one alters a design or a documented behaviour and needs its own
decision:

- The query is taken from the second positional argument when there are two or
  more positional arguments. This suits methods, where the first argument is the
  instance, but it is a heuristic for plain functions. Changing it changes which
  value is recorded (`decorators/traced_retrieval/traced_retrieval_client.py`).
- The public-method selection helper is the same as the one in domain_monitoring.
  The two roots do not depend on each other, so sharing it would add a dependency
  between roots; kept duplicated.
- Declaration checks for `principal_id` and `session_id` accept any non-empty
  string. Format rules for identifiers are a policy decision and are not added here.
- Method docstrings were neither added nor removed, pending a decision on
  method docstrings.
- `Optional[...]` annotations are kept to match the other roots of the
  distribution.

## Gate results

Commands were run from the worktree of the pass branch, after the last source change.

- `uv run --python 3.12 pytest -v --cov --cov-fail-under=100`: 756 passed; coverage 100.00 percent. Base before this pass: 738 passed, 100.00 percent.
- `uv run --python 3.14 pytest -v --cov --cov-fail-under=100`: 756 passed; coverage 100.00 percent.
- `uv run --python 3.12 mypy domain_aspects/ domain_rag/`: Success: no issues found in 63 source files.
- `uvx ruff@0.15.14 check .`: All checks passed!
- `uvx ruff@0.15.14 format --check .`: 248 files already formatted. The format exclude for the relocated version test was removed in this pass.
- `strict-module` at strict-suite 0.4.0 over the six package roots: exit 0 for each root, with no findings.
- `strict-module loc-cap` over the six package roots: within the 300 LOC cap for each root.
- `uv lock --check`: exit 0. The lock file did not change.
- Markdown dash grep: no matches. Markdown hygiene greps: no matches.
- Attribution grep over the commits of this pass: no matches.

Test counts in this root: monitoring base 48 collected, now 55; retrieval base 45 collected, now 55.
