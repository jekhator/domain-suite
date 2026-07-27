# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Aspect import error messages corrected**: Rewrote three misleading error messages in `domain_aspects.services.constants.aspects`: `ERR_ASPECT_REQUIRES_IMPORT_MISSING`, `ERR_ASPECT_TENANT_SCOPED_IMPORT_MISSING`, and `ERR_ASPECT_THROTTLED_IMPORT_MISSING` now correctly state that domain-security and domain-api-limiter are built into domain-suite (not external packages with non-existent extras); messages now direct users to reinstall domain-suite rather than non-existent [security] or [throttle] extras. All seven ERR_ASPECT_*_IMPORT_MISSING constants audited against pyproject.toml extras; logging and sensitivity extras verified correct; hard-dependency messages (domain-errors, domain-monitoring) remain unchanged.
- **Strict-suite CI pin bump to 0.4.0**: Updated `.github/workflows/strict-module.yml` strict-module and loc-cap invocations from `strict-suite==0.3.0` to `strict-suite==0.4.0`; R001-R011 rule set unchanged so no new violations surface; all six domain roots remain fully compliant.
- Wheel no longer ships conftest/test-constants files.

## [0.3.1] - 2026-07-18

### Fixed

- **Optional-dependency extras repoint**: Fixed broken `[logging]`, `[sensitivity]`, and `[all]` extras in pyproject.toml that incorrectly referenced non-existent standalone distributions `mixin-logging>=0.6.0` and `mixin-sensitivity>=0.4.0` (import roots exist only inside mixin-suite). Repointed all extras to `mixin-suite>=0.3.0` for correct PyPI resolution; `[all]` now also includes `boto3>=1.28.0` for cloudwatch sink access.
- **Constants sweep in domain-monitoring**: Extracted magic strings from `domain_monitoring/services/metrics/cloudwatch_sink.py` into module constants: `DEFAULT_CLOUDWATCH_NAMESPACE` ("domain-monitoring"), `CLOUDWATCH_METRIC_UNIT` ("Milliseconds"), `CLOUDWATCH_DIMENSION_OUTCOME` ("Outcome") in `domain_monitoring/services/constants/metrics.py`. CloudWatchMetricSink now uses named constants instead of inline strings for namespace default and metric field values; AWS API boundary TypedDict keys and put_metric_data kwargs left untouched (API contract).
- **Strict-suite CI pin upgrade to 0.3.0**: Updated `.github/workflows/strict-module.yml` strict-module and loc-cap invocations from `strict-suite==0.2.0` to `strict-suite==0.3.0`; R001-R011 rule set unchanged so no new violations surface; all six domain roots remain fully compliant.

## [0.3.0] - 2026-07-17

### Added

- **domain-monitoring label injection**: `@monitored` decorator now accepts opt-in `labels_from_result` and `labels_from_exc` callbacks to populate metric event labels dynamically on success and failure. Callbacks receive result or exception and return tuple of (key, value) label pairs; absent callbacks default to empty labels for backward compatibility. Works with sync/async callables and class decoration with method fan-out.
- **CloudWatchMetricSink**: Production-ready metric sink emitting `MetricEvent` to AWS CloudWatch via boto3. Accessible via optional `domain-suite[cloudwatch]` dependency; raises clear ImportError if boto3 missing. Emits metric name, duration, outcome dimension, and any label dimensions to CloudWatch. Uses configurable namespace (default: `domain-monitoring`).

### Fixed

- **domain-aspects export**: Added missing `Monitored` aspect entry to root `__all__` and public imports; previously implemented but unreachable from `from domain_aspects import Monitored`. Added lockstep test verifying public API export.
- **Per-root version consistency**: Unified all six domain roots (`domain_errors`, `domain_security`, `domain_api_limiter`, `domain_monitoring`, `domain_aspects`, `domain_rag`) to report identical `__version__ = "0.3.0"`. Added cross-root version consistency test to prevent future drift.
- **Monitored marker label parity**: Monitored aspect marker now accepts `labels_from_result` and `labels_from_exc` callbacks for feature parity with the `@monitored` decorator; aspect-path composition can now extract and emit dynamic labels matching decorator behavior. ASPECT_ORDER exported from package root for public consumption.

## [0.2.0] - 2026-07-14

### Added

- **domain-aspects**: Monitored aspect entry composing `domain-monitoring` decorator into the aspect container. Follows suite-wide class-capable standard with target-polymorphic decoration, class fan-out over public own methods, root+method-name derivation, override=replace via marker attribute, and frozenset consts for container config. Includes unit and REAL-dependency integration tests with composition test for stacking with other aspects.
- **domain-rag**: Vendor-neutral retrieval provenance wrapper with HIPAA-auditable audit trails. Emits `RetrievalProvenance` (query, chunk_ids, source_document_ids, principal_id, session_id, outcome, duration) via `@traced_retrieval` decorator. Includes `ProvenanceSink` protocol, `NullProvenanceSink` (default), `CollectingProvenanceSink` (testing), and `ProvenanceRegistry` for global sink binding. Supports sync/async callables and class decoration with method fan-out. Never swallows exceptions. 100% coverage with real tests covering sink collection, decorator invocation, registry binding, and sync/async paths.
- **Test coverage to 100%**: Statement coverage across all six packages raised from 95% to 100%; real tests added for classmethod/staticmethod decoration in `@monitored` and nested class handling in `@tenant_scoped`. Unreachable code paths (ImportError in aspects_objects.py, classmethod/staticmethod descriptor checks in monitored_client.py) marked with `# pragma: no cover`. CI threshold (`--cov-fail-under`) ratcheted to 100.

### Changed

- **Strict-suite upgraded to 0.2.0**: Updated CI pin to strict-suite 0.2.0 with R009/R011 fixes (return-in-try/except block refactoring, unreachable code detection); all six domain roots remain compliant with zero module violations.
- **Python 3.14 CI matrix**: Expanded test matrix to Python 3.14; classifier added; CI gating validates all six roots on Python 3.11 and 3.14.

### Fixed

- **Const-alias and conformance fixes**: Extracted inline ValueError and related exception literals to ERR_* constants throughout domain-suite per cross-pkg standard; removed redundant `__hash__` methods from frozen dataclasses; modernized type annotations including `typing.Self` usage.
- **Module structure conformance**: Added docstrings and re-exports to all empty `__init__.py` files across domain-suite per per-dir-type convention: group-level dirs (decorators, services, config, errors, common) receive one-line docstrings; concern-package dirs (e.g., monitored, metrics, registry) receive docstrings plus absolute re-exports and `__all__`; constants-dir files remain intentionally empty; test-dir files receive descriptive one-line docstrings for discoverability.
- **CI/Workflow**: Expanded `strict-module.yml` to lint and LOC-cap all six import roots (domain-errors, domain-security, domain-api-limiter, domain-monitoring, domain-aspects, domain-rag) instead of domain-aspects alone. Each root now gated by strict-module and LOC violations in any root fail CI.

## [0.1.1] - 2026-07-11

### Fixed

- Documentation conformance release: README badges and per-package run-verified examples, docs index, docs tree renamed to full package names, dash and terminology sweeps, and removal of internal artifacts. No code changes.

## [0.1.0] - 2026-07-09

### Added

- **Monorepo consolidation**: Consolidated five domain packages into a single distribution:
  - `domain-errors` 0.2.0: Typed domain error hierarchy with wrapping and chaining
  - `domain-security` 0.2.0: Security context management and authorization checks
  - `domain-api-limiter` 0.2.0: Request rate limiting and quota enforcement
  - `domain-monitoring` 0.1.0: Event monitoring and telemetry
  - `domain-aspects` 0.1.1: Composable decorators for cross-cutting concerns

- **Unified testing**: Consolidated pytest configuration, coverage tracking, and test discovery across all five packages. Merged root conftest fixtures for security context and monitoring registry reset.

- **Unified CI/CD**: Single `.github/workflows/` with six shared workflows:
  - `ci.yml`: Full test suite with coverage reporting
  - `cleanup-guard.yml`: Directory structure validation
  - `strict-module.yml`: Per-package DTO validation and line-count gatekeeping
  - `no-ai-attribution.yml`: Attribution verification (blocks AI-assistant attribution markers in commits and PRs)
  - `publish.yml`: PyPI publication via trusted publishers (gated by James)
  - `ruff.yml`: Linting and formatting checks

- **Dynamic versioning**: All five packages version-locked to `0.1.0` via `domain_errors/config/_version.py`, with hatch dynamic resolution in unified `pyproject.toml`.

- **Dissolved inter-package dependencies**: `domain-errors`, `domain-security`, `domain-api-limiter`, and `domain-monitoring` are no longer external dependencies within the distribution (imports resolve within the bundled `domain-suite` dist). `domain-aspects` optional extras re-scoped: `logging` (external `mixin-logging>=0.6.0`), `sensitivity` (external `mixin-sensitivity>=0.4.0`), `all` (both external packages).

- **Test consolidation**: Migrated all `domain-aspects` tests from top-level `tests/test_aspects/` into `domain_aspects/services/tests/test_aspects/` per concern-scoped layout. Single merged root `conftest.py` houses autouse fixtures for security context reset and monitoring registry reset.

- **Documentation structure**: Per-package documentation in `docs/<package>/` with historical changelogs preserved as `CHANGELOG-history.md`.

### Changed

- **domain-errors**: Renamed `DEFAULT_MESSAGE` constant to `ERR_DOMAIN_UNSPECIFIED` in `domain_errors/domains/constants/domain_error.py` for naming uniformity with the ERR_<DOMAIN>_<CONDITION> convention used across domain packages.
- **Package structure**: No API changes to any package; purely organizational consolidation.

### Internal

- Single `pyproject.toml` with unified build configuration, test paths, coverage tracking, and tool settings.
- Shared `.github/workflows/` for CI/CD across all five packages.
- Root `uv.lock` coordinating dependencies for all packages.

---

For detailed changes to individual packages before consolidation, see:

- `docs/domain_errors/CHANGELOG-history.md`
- `docs/domain_security/CHANGELOG-history.md`
- `docs/domain_api_limiter/CHANGELOG-history.md`
- `docs/domain_monitoring/CHANGELOG-history.md`
- `docs/domain_aspects/CHANGELOG-history.md`
- `docs/domain_rag/CHANGELOG-history.md` (first release in domain-suite 0.1.1+)
