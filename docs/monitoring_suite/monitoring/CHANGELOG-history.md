# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

## [0.1.0] - 2026-07-07

### Added

- Initial release: MetricEvent DTO for structured metric observation
- MetricSink protocol with CollectingSink and NullSink implementations
- @monitored decorator for automatic per-method metrics on sync and async callables
- Class-level @monitored with automatic fan-out to public methods
- MonitorRegistry for global default sink binding
- Comprehensive test coverage (95%+)
- Type hints and PEP 561 compliance
