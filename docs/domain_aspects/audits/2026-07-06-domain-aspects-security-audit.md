# Security Audit: domain-aspects 0.1.0

Date: 2026-07-06

## Scope

Security review of domain-aspects package v0.1.0: aspect entry objects, composition service, and error handling.

## Findings

### Aspect Entry Validation

All entry objects validate their fields in `__post_init__`:

- `Logged.event`: non-empty string check.
- `Requires.permission`: non-empty string check.
- `TenantScoped.param_name`: non-empty string check.
- `Throttled.scope`, `rate`: non-empty string checks; tiers must be tuple.
- `WrapErrors.as_`: must be a type (exception class); catch must be non-empty tuple of exception types.
- `Sensitive`: no fields to validate.

### Declaration-Time Validation

Aspects service validates at decoration time:

- No duplicate aspect kinds allowed (would mask one with another).
- Unknown entry types rejected (type-safe composition).
- Empty declarations rejected (nonsensical decoration).

### Lazy Import Pattern

Optional dependencies are imported only in entry `build()` methods, not at module load:

- Entries are validatable and hashable without optional deps.
- Missing optional deps raise clear ImportError with guidance (e.g., "add [security] extra").
- Hard dependency (domain-errors) is always available.

### Exception Handling

AspectDeclarationError is raised for validation failures at decoration time, preserving traceability.

### Multi-Target Support

Aspects decorator is target-polymorphic: works on functions and classes. Underlying suite decorators (logging-mixin, domain-security, domain-api-limiter, mixin-sensitivity, domain-errors) all support both, so no special fan-out logic needed.

## Conclusion

No security concerns identified. Aspects service correctly enforces declaration-time validation, lazy-loads optional dependencies, and composes decorators in standard order.
