# domain-monitoring optimization pass (2026-10-19)

## Purpose

This optimization pass reviews every Python module and test module of the
domain_monitoring package against correctness, dead and duplicated code,
control flow, typing, constants, naming, formatting, performance and test
quality. Each file was read in full. Changes that alter observable behaviour
are listed under Behavior changes and in the 0.7.0 section of the changelog;
the remaining changes are code hygiene. Exported names, event names, the
message constants and the public decorator signature are unchanged.

Scope: 35 Python files under domain_monitoring/ (22 source and 13 test
files) at the base commit, plus the package README and architecture page.
Gate results are recorded at the end of this document.

## Behavior changes

1. A failing sink or a failing `labels_from_exc` callback no longer replaces
   the monitored call's exception. The recording error is attached to the
   exception as a note (`Exception.add_note`). The exception type and message
   are unchanged.
2. The success event is emitted after the call returns, outside the exception
   handling path. A sink error on a successful call is raised once, and it is
   no longer also recorded as a failed call.
3. Durations use `time.perf_counter()`. A backwards step of the wall clock can
   no longer produce a negative duration that the event constructor rejects.
4. Class decoration wraps the public functions and method descriptors defined
   on the decorated class. An overridden method is now monitored. A method
   inherited from a base class is not wrapped by the class decorator.
5. Classmethods and staticmethods on a monitored class keep their descriptor
   type. Previously the wrapper was bound as an instance method, so a call
   through an instance failed.
6. `@monitored` rejects an empty event name when it is applied, with
   `MonitoringDeclarationError`.
7. A bound sink that evaluates as falsy is used. Only an unset sink selects the
   registry default.

## Changes

- The success and failure paths share helpers for label building, event
  construction and emission; the sync and async wrappers differ only in the
  await.
- Correlation label names, the domain lane suffix and the failure-note text
  live in the metrics constants module, referenced through the const alias.
- The CloudWatch import guard in the package root and the unreachable
  `pragma: no cover` branches were removed.
- `MonitorRegistry` keeps one shared null sink instead of building one per
  lookup.
- Tests now assert on the constants, use `pytest.raises` for every failure
  check, cover the recording behaviour above, and no longer contain a
  no-op assertion or a test that proves nothing.
- The package README and the monitoring flow-trace page describe the current
  API; their printed outputs are real runs at 0.7.0.

## Per-file review

| path | findings | changed | note |
| --- | --- | --- | --- |
| domain_monitoring/__init__.py | 1: ImportError guard around the CloudWatch import could never fire (the sink imports boto3 lazily) | yes | guard removed; the export is unchanged |
| domain_monitoring/common/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/common/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/common/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/config/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/config/_version.py | none | yes | version bump to 0.7.0 |
| domain_monitoring/conftest.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/decorators/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/decorators/monitored/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/decorators/monitored/monitored_client.py | 12: failure recording could replace the call's exception (fixed); wall-clock durations can go negative (fixed); sync and async bodies duplicated (fixed); falsy sink selected by `or` (fixed); empty event name accepted (fixed); classmethod and staticmethod rewrapped as instance methods (fixed); inherited base methods excluded by a first-base name check, overrides skipped (fixed); dead descriptor branches marked no cover (removed); untyped public list (typed); repeated label callback types (type aliases); correlation literals in code (constants); NullSink built per call (registry) | yes | shared emit helpers; failure path keeps the exception; success events emitted after the call; class fan-out over own functions and descriptors; see Behavior changes |
| domain_monitoring/errors/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/errors/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/errors/constants/monitoring.py | 2: section labels written as bare string expressions (converted to comments); empty-event message constant missing (added) | yes | constants added for the empty event name |
| domain_monitoring/errors/monitoring_errors.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/services/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/services/constants/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/services/constants/metrics.py | 1: correlation label names, the lane suffix and the failure-note text were literals in the decorator (moved here) | yes | new constants referenced through the const alias |
| domain_monitoring/services/metrics/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/services/metrics/cloudwatch_sink.py | 2: pragma no cover on a reachable ImportError branch (removed; now tested); put_metric_data accepts at most 30 dimensions while labels are unbounded (candidate, deferred) | yes | pragma removed; dimension limit deferred |
| domain_monitoring/services/metrics/metrics_client.py | 1: redundant pass after the NullSink docstring (removed) | yes | no behaviour change |
| domain_monitoring/services/metrics/metrics_objects.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/services/registry/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/services/registry/registry_client.py | 2: default sink chosen by truthiness, so a falsy sink was replaced (fixed); NullSink constructed on every lookup (shared instance) | yes | identity check; class-level fallback instance; typed ClassVar state |
| domain_monitoring/tests/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_metrics/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_metrics/conftest.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_metrics/test_cloudwatch_sink.py | 2: missing-boto3 test replaced the constructor with a copy and proved nothing (rewritten to hide boto3); literal unit, dimension and namespace values (constants) | yes | real import failure path exercised |
| domain_monitoring/tests/test_metrics/test_metrics_client.py | 1: no-op assertion `assert True` (replaced with a check that the null sink keeps no state) | yes | assertion strengthened |
| domain_monitoring/tests/test_metrics/test_metrics_objects.py | 2: validation messages written as literals (constants); test name misdescribes the assertion (renamed) | yes | match uses the metrics constants |
| domain_monitoring/tests/test_monitored/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_monitored/conftest.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_monitored/test_monitored_client.py | 4: no tests for a failing sink on the failure path, a failing labels callback, a success-path sink error, or an empty event name (added); no test that classmethods stay bound on instances (added); no test for own-method fan-out versus inherited methods (added) | yes | new test class covering the recording behaviour |
| domain_monitoring/tests/test_registry/__init__.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_registry/conftest.py | none | no | reviewed against every lens; no finding |
| domain_monitoring/tests/test_registry/test_registry_client.py | 1: no test for a falsy bound sink (added) | yes | new test |

## Deferred candidates

These were recorded during review and deliberately not changed in this pass,
because each one alters a design or a documented behaviour and needs its own
decision:

- `CloudWatchMetricSink` sends every label as a dimension. CloudWatch accepts at
  most 30 dimensions per metric, so an event with more labels is rejected by
  the service. Limiting or validating labels changes what is emitted
  (`services/metrics/cloudwatch_sink.py`).
- The public-method selection helper is the same as the one in domain_rag. The
  two roots do not depend on each other, so sharing it would add a dependency
  between roots; kept duplicated (`decorators/monitored/monitored_client.py`).
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
