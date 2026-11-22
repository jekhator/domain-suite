# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-06

### Added

- **Class-level @throttled decoration**: Apply @throttled to a class to fan out per-method policies.
  - Each public method gets a policy with scope `{root}:{method_name}`.
  - Private methods (_-prefixed), dunders, properties, and nested classes are skipped.
  - Methods already decorated with @throttled retain their individual policies (override-replace semantics).
  - Supports classmethod and staticmethod decorators alongside instance methods.
  - Base rate and tier overrides propagate uniformly to all fanned-out methods.
  - Validates that decorated classes have at least one public method (raises `ThrottleDeclarationError` if empty).
- Extended `PolicyRegistry.collect()` to properly handle classmethod and staticmethod descriptors.
  - Ensures policies from fanned-out class-level decorations are collected in definition order.
- New error constant `ERR_POLICY_NO_PUBLIC_METHODS` for validation of empty classes.

## [0.1.0] - 2026-07-06

### Added

- `Period` StrEnum with SECOND, MINUTE, HOUR, DAY values for rate periods.
- `RateLimit` frozen dataclass for parsed rates with N/period parsing and serialization.
  - `from_rate(rate: str)` class method to parse N/period rate strings.
  - `period_seconds` property to convert periods to seconds.
  - `as_rate()` method to round-trip serialize back to N/period form.
- `TierRate` frozen dataclass for per-tier rate overrides with tier label and rate.
- `ThrottlePolicy` frozen dataclass for complete throttle declarations with scope, base rate, and tier overrides.
  - `rate_for(tier: str)` method to resolve tier overrides or return base rate.
  - `has_tiers` property to check if tier overrides are declared.
- `@throttled(scope, rate, tiers=None)` decorator for declarative policy attachment to methods.
  - Validates scope, rate, and tier strings at decoration time.
  - Attaches policy metadata without changing method signature or behavior.
  - Supports tier overrides via `tiers={"free": "10/day", "pro": "1000/hour"}` mapping.
- `PolicyRegistry` class for policy introspection and collection.
  - `policy_of(target)` method to retrieve a policy from a single callable.
  - `collect(container)` method to retrieve all policies from a class or module in definition order.
- `ThrottleError` base error class (domain="api_limiter", http_status=429, retryable=True).
- `RateLimitExceeded` error for rate-limit violations (code="rate_limit_exceeded").
- `ThrottleDeclarationError` error for malformed policy declarations at import time (http_status=500, retryable=False).
  - Validates non-positive request counts, malformed rate strings, unknown periods, empty scopes, empty tier labels, and duplicate tier labels.
- Full test coverage for all value objects, decorators, registry, and error types.
- Comprehensive documentation in README.md and docs/apps/ with runnable examples.
