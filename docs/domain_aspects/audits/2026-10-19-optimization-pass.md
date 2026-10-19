# domain-aspects optimization pass (2026-10-19)

## Purpose

This optimization pass reviews every Python module of the domain_aspects
package, including its test modules, against correctness, dead and duplicated
code, control flow, typing, constants, naming, formatting, performance and test
quality. Each file was read in full. Findings that change observable behaviour
are listed in the Behavior changes section and in the changelog; every other
change is code hygiene. Exported names, the aspect order, the message constants
that tests and documentation match against, and the composition surface are
unchanged except where listed.

Scope: 28 Python files under domain_aspects/ at the base commit (17 source and
11 test modules, counting package initialisers). Two modules were added (the
class-level helper and the aspect kind enumeration), so the per-file table has
30 rows, one for every Python file in the package tree at the end of the pass.

## Behavior changes

1. `Logged` on a call whose `mixin-logging` package is missing now raises
   `ImportError` with the add-extra guidance from the constants module. It
   previously raised `ModuleNotFoundError` naming the module, and the guidance
   constant was never raised.
2. A failure raised while emitting the end event of a logged call is no longer
   recorded as an operation error. The operation's own exceptions still emit the
   error event and propagate unchanged. Previously an emission failure after a
   successful call was logged as an error and then re-raised.
3. The unreachable dynamic-policy guard in the retry builder raises `ValueError`
   rather than relying on `assert`, which optimized interpreters remove.
4. The public export list is sorted. The names are unchanged.

## Changes

- The class-level walk shared by the logged and retried builders moved into one
  helper class in a new module; both builders call it.
- The logged wrapper emits events through one emitter object. The async and sync
  bodies share the emitter rather than repeating payload, logging and latency
  handling inline.
- `AspectKind` moved to its own module so entry objects no longer import inside
  a property. The name is still importable from the entry-objects module.
- The aspect order is indexed once per composition service class instead of
  being rebuilt on every composition, and unknown kinds sort after the known
  ones through a named rank rather than a literal.
- The duplicated error constants in the service constants module were removed;
  the composition service refers to the errors constants module, which already
  owns them.
- The logged and retried marker attribute names moved to the constants module.
- Type annotations: `Optional[...]` became `X | None`; payload extractors are
  typed as returning a mapping of strings to objects rather than bare `dict`.
- Test modules: match patterns use the constants module (escaped where the
  message holds regex characters); per-test imports moved to module level;
  repeated error-class and sink definitions became module-level helpers; a
  duplicate composition test and a wrong count in two docstrings were corrected;
  the logged wrapper tests now record the ambient log calls and assert event
  names, payloads and latency fields; the import-missing tests assert the
  guidance constants; a misplaced type ignore was removed.

## Per-file review

| path | findings | changed | note |
| --- | --- | --- | --- |
| domain_aspects/__init__.py | 1: export list unsorted | yes | sorted; names unchanged |
| domain_aspects/config/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/config/_version.py | none | no | version bump belongs to the release step |
| domain_aspects/conftest.py | none | no | root conftest holds no fixtures |
| domain_aspects/errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/errors/aspects_errors.py | none | no | reviewed against every lens; no finding |
| domain_aspects/errors/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/errors/constants/aspects.py | none | no | owns the composition error messages; referenced by the service |
| domain_aspects/services/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/services/aspects/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/services/aspects/aspects_class_fanout.py | new helper for the class-level walk | added | shared by the logged and retried builders |
| domain_aspects/services/aspects/aspects_client.py | 5: dead TYPE_CHECKING block; literal rank for unknown kinds; order index rebuilt per composition; isinstance tuple repeats the union; duplicated error constants | yes | block removed; named rank; class-level index; union read with get_args; errors constants module referenced |
| domain_aspects/services/aspects/aspects_kind.py | new module for the aspect kind enumeration | added | the entry-objects module re-exports the same name |
| domain_aspects/services/aspects/aspects_logged_builders.py | 6: async and sync bodies duplicated; per-call payload plumbing repeated; truthiness check on the latency clock; parameter named cls in a static method; marker literal in module; missing-extra guidance not raised | yes | one emitter; shared class walk; is-not-None checks; target_class; constants module; guidance raised |
| domain_aspects/services/aspects/aspects_objects.py | 4: Optional annotations; bare dict in extractor types; inline kind enumeration; unneeded pragma on the monitored import guard | yes | X or None; mapping types; kind moved; pragma removed (covered by the import-missing test) |
| domain_aspects/services/aspects/aspects_require_mixins.py | 1: per-call import inside the kind property | yes | import moved to module level via the new kind module |
| domain_aspects/services/aspects/aspects_retried_builders.py | 4: assert used as a narrowing guard; class walk duplicated; marker literal in module; Optional annotations | yes | explicit guard with a single-line invariant note; shared walk; constants module; X or None |
| domain_aspects/services/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/services/constants/aspects.py | 4: duplicated error constants; non-ASCII arrow in a docstring; marker literals in module; over-long message line | yes | duplicates removed; arrow replaced; markers added; message wrapped |
| domain_aspects/services/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/services/tests/test_aspects/__init__.py | none | no | reviewed against every lens; no finding |
| domain_aspects/services/tests/test_aspects/conftest.py | 1: no fixture for the ambient log calls | yes | captured-log fixture added; existing fixtures unchanged |
| domain_aspects/services/tests/test_aspects/test_aspects_client.py | 4: misplaced type ignore; literal match strings; per-test import; duplicate test and wrong count in docstrings | yes | constants used; import hoisted; duplicate removed; docstrings corrected |
| domain_aspects/services/tests/test_aspects/test_aspects_integration.py | 5: imports inside most tests; error class redefined per test; sink class redefined per test; retry policy repeated; class name that pytest could collect | yes | module-level imports and helpers; typed failure renamed to avoid collection |
| domain_aspects/services/tests/test_aspects/test_aspects_logged_wrapper.py | 3: assertions only on return values; test names claim latency that is not checked; no log assertions | yes | ambient log calls recorded and asserted |
| domain_aspects/services/tests/test_aspects/test_aspects_objects.py | 3: literal match strings; per-test imports; retry policy repeated | yes | constants used; import hoisted |
| domain_aspects/services/tests/test_aspects/test_aspects_retried_wrapper.py | 1: retry policy literal repeated across the aspects test modules | no | deferred; see Deferred candidates |
| domain_aspects/services/tests/test_aspects/test_coverage_100pct.py | 1: docstring describes a case with one extractor as several | yes | docstring corrected |
| domain_aspects/services/tests/test_aspects/test_coverage_gaps.py | 1: docstrings cite source line numbers | yes | line references removed |
| domain_aspects/services/tests/test_aspects/test_import_missing_safe.py | 2: literal match strings; logged test expected a module error instead of the guidance | yes | constants used with escaped matches; logged test asserts the guidance |

## Deferred candidates

These were recorded during review and deliberately not changed in this pass,
because each one alters a design or a type owned by another package:

- `WrapErrors.build` keeps its `# type: ignore[arg-type]`: the parameter type of
  the wrap_errors decorator belongs to the domain-errors package
  (`services/aspects/aspects_objects.py`).
- Dynamic retry policies call `RetryExecutor.wrap` on every call. Caching the
  wrapped callable per policy is a design change with its own identity rules
  (`services/aspects/aspects_retried_builders.py`).
- The test modules `test_coverage_100pct.py` and `test_coverage_gaps.py` are
  named for coverage rather than for the concern they test. Renaming them changes
  test identifiers, so it is left for a separate change.
- The retry policy literal in `test_aspects_retried_wrapper.py` repeats the one
  in the other aspects test modules. Sharing it through conftest would couple
  the modules, so it is left as is.

## Gate results

Commands were run from a checkout of the pass branch with the locked dependency set.

- `uv run pytest -v --cov --cov-fail-under=100` on Python 3.12 and 3.14: 738
  passed in each run for the whole suite, coverage 100.00 percent.
- Tests before and after, per root: domain_aspects 146 before and 145 after
  (the whole-suite figure also includes the other roots).
- `uv run mypy domain_aspects/ domain_rag/`: no issues in 63 source files.
- `uvx ruff@0.15.14 check .`: all checks passed.
- `uvx ruff@0.15.14 format --check . --exclude test_version_consistency.py`: 247
  files already formatted.
- `strict-module` at strict-suite 0.4.0 over the six package roots: exit 0 for
  each root.
- `strict-module loc-cap` over the six package roots: every root within the 300
  LOC cap; the soft-target warning remains for the logged builders and the
  entry-objects module.
- Markdown dash grep: no matches.
- Attribution grep over the commits of this pass: no matches.
