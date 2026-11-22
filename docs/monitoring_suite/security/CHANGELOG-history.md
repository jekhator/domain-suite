# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-06

### Added

- Class-level application of @requires and @tenant_scoped decorators
- Decorators applied to a class automatically wrap all public methods
- Selection rules for class-level decoration: skips private methods (prefixed with `_`), dunder methods, properties, and nested classes
- Override detection: methods already decorated with the same decorator are not re-wrapped
- Declaration-time fast-break for @tenant_scoped: raises SecurityDeclarationError if any public method lacks the tenant parameter at class-level decoration
- SecurityDeclarationError for decorator declaration-time validation failures
- Support for classmethod and staticmethod in class-level decoration via unwrap-rewrap pattern
- Marker attributes to track decorator application (__requires_decorated__, __tenant_scoped_decorated__)

## [0.1.0] - 2026-07-04

### Added

- SecurityContext and Principal frozen dataclasses for ambient identity and tenant boundaries
- SecurityContextManager for set/get/bind/clear of ambient context via ContextVar
- Authorizer class with check() and require() for scope-based permission enforcement
- Permission and PolicyDecision value objects for authorization decisions
- TenancyGuard for tenant-boundary enforcement
- @requires decorator for declarative permission checks on methods
- @tenant_scoped decorator for declarative tenant-boundary enforcement
- SecretRef and SecretValue for lazy, masked secret resolution
- SecretsBackend Protocol for pluggable secret fetching
- SecurityError base exception with subclasses AuthzError, TenancyError, SecretError
- All errors integrate with domain-errors for structured logging and HTTP status codes
