# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-07-07

### Fixed

- Fixed WrapErrors.build() to pass catch as keyword-only argument to wrap_errors decorator (caught argument order issue).
- Added comprehensive real-deps integration tests for all six aspects (Logged, Requires, TenantScoped, Throttled, WrapErrors, Sensitive) on both function and class targets.

## [0.1.0] - 2026-07-07

### Added

- AspectKind enum with six aspect kinds: LOGGED, REQUIRES, TENANT_SCOPED, THROTTLED, WRAP_ERRORS, SENSITIVE.
- Entry value objects (all frozen dataclasses with hashable fields for frozenset membership).
  - Logged: lazy-import logging mixin, emit event on entry and exit.
  - Requires: permission check via domain-security.
  - TenantScoped: tenant isolation enforcement via domain-security.
  - Throttled: rate limiting via domain-api-limiter.
  - WrapErrors: exception wrapping and translation via domain-errors.
  - Sensitive: sensitive field masking via mixin-sensitivity.
- Aspects service class (stateless): compose and apply aspect decorators in canonical order.
  - Flattens frozensets and single entries.
  - Validates duplicate kinds, unknown entry types, and empty declarations.
  - Sorts by ASPECT_ORDER before applying (innermost-first application).
  - Module-level entrypoint: aspects constant.
- Comprehensive test coverage (100% for objects, 95%+ for client).
  - Entry validation (non-empty strings, type checks).
  - Hashability verification for frozenset membership.
  - Flatten/validate/sort paths (duplicate kind, unknown type, empty declaration).
  - Ordering verification (application order matches ASPECT_ORDER regardless of declaration order).
  - Lazy-import isolation (entries importable without optional deps; build() raises clear error).
  - Integration tests with real deps installed (logged events, tenant fast-break, policies, error wrapping, sensitive repr).
  - Singular-entry and frozenset forms.
  - Function and class targets.
- Documentation: README with run-verified example, feature docs, security audit, code review artifacts.
