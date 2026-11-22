# @throttled Decorator and Policy Registry

## Purpose

The `@throttled` decorator attaches immutable throttle policies to methods, validating policy constraints at decoration time. PolicyRegistry then introspects methods and classes to collect declared policies, returning them in definition order so adapters can build framework-level throttling (Django REST Framework throttles, middleware, etc.).

Declaration is not enforcement: the decorator never enforces rate limits itself. Enforcement is the responsibility of the consuming framework's vetted throttling logic. This separation keeps concerns clean: the decorator declares *what* policies apply; the framework implements *how* to enforce them.

## Behavior

### @throttled Decorator

```python
from monitoring_suite.api_limiter import throttled

@throttled(scope: str, rate: str, tiers: Mapping[str, str] | None = None)
def my_method() -> None:
    pass
```

The decorator:
1. Parses the scope and rate strings.
2. Constructs a ThrottlePolicy with tier overrides (if provided).
3. Validates the policy (scope and rate are valid; tier labels are unique).
4. Attaches the policy to the method via `__throttle_policy__` attribute.
5. Returns the method unchanged: the decorated method has the same signature and behavior.

Validation happens at decoration time, so invalid policies fail at import before any code runs.

#### Parameters

- `scope` (str): A policy identifier, typically hierarchical (e.g., "docs:list", "api:call", "payments:charge"). Must be non-empty.
- `rate` (str): A rate string in the form "N/period", where N is a positive integer and period is one of second, minute, hour, day (e.g., "100/hour", "20/minute", "10/day").
- `tiers` (Mapping[str, str] | None): Optional per-tier rate overrides. Maps tier label to rate string (e.g., {"free": "10/day", "pro": "1000/hour"}). Tier labels must be unique and non-empty. If not provided, no tier overrides are declared.

#### Examples

```python
from monitoring_suite.api_limiter import throttled

class DocumentService:
    # Base rate, no tiers
    @throttled("docs:list", "100/hour")
    def list_documents(self, tenant_id: str) -> list:
        return []

    # Base rate with tier overrides
    @throttled(
        "docs:upload",
        "20/minute",
        tiers={"free": "10/day", "pro": "1000/hour"}
    )
    def upload(self, tenant_id: str, file_path: str) -> str:
        return "doc123"

    # Multi-level scopes
    @throttled("account:transfer", "5/hour", tiers={"basic": "1/hour"})
    def transfer(self, amount: float) -> None:
        pass
```

### Policy Registry

`PolicyRegistry` walks callables and classes to collect declared policies. It reads the `__throttle_policy__` attribute attached by the decorator and returns policies in definition order.

```python
from monitoring_suite.api_limiter import PolicyRegistry

registry = PolicyRegistry()

# Retrieve a policy from a single callable
policy = registry.policy_of(my_method)

# Collect all policies from a class
policies = registry.collect(DocumentService)

# Collect all policies from a module
import my_module
policies = registry.collect(my_module)
```

#### policy_of(target)

Returns the policy attached to a single callable, or None if no policy is declared.

```python
from monitoring_suite.api_limiter import PolicyRegistry, throttled

@throttled("api:call", "100/hour")
def my_func():
    pass

registry = PolicyRegistry()
policy = registry.policy_of(my_func)  # ThrottlePolicy(scope="api:call", ...)

policy = registry.policy_of(lambda: None)  # None (no policy)
```

#### collect(container)

Returns all policies declared on a class or module's members, in definition order. Only callable members are inspected; non-callables are skipped.

```python
from monitoring_suite.api_limiter import PolicyRegistry, throttled

class MyService:
    @throttled("op:first", "100/hour")
    def first_method(self):
        pass

    def undecorated_method(self):
        pass

    @throttled("op:second", "50/minute")
    def second_method(self):
        pass

registry = PolicyRegistry()
policies = registry.collect(MyService)

print(len(policies))        # 2
print(policies[0].scope)    # "op:first"
print(policies[1].scope)    # "op:second"
```

Policies are returned in the order they appear in the class or module definition.

## Public Surface

### Decorator

```python
def throttled(
    scope: str,
    rate: str,
    tiers: Mapping[str, str] | None = None
) -> Callable[[T], T]:
    """Return a declaration decorator for the scope, rate, and tier overrides."""
    pass
```

Returns a decorator that attaches a validated ThrottlePolicy to a callable without changing its signature or behavior.

### PolicyRegistry

```python
class PolicyRegistry:
    def policy_of(self, target: Callable[..., object]) -> ThrottlePolicy | None:
        """Return the policy declared on the target, or None."""

    def collect(
        self,
        container: type | ModuleType
    ) -> tuple[ThrottlePolicy, ...]:
        """Return the policies declared on a class or module's members, in definition order."""
```

## Constants

### From `monitoring_suite.api_limiter.services.constants.policy`

```python
THROTTLE_POLICY_ATTR: Final = "__throttle_policy__"
```

The attribute name that the decorator uses to attach policies. Exposed for integration testing or custom introspection tools.

## Error Semantics

All validation errors are raised at decoration time:

- `ThrottleDeclarationError` with message "rate requests must be positive" when the rate count is non-positive.
- `ThrottleDeclarationError` with message "rate must use the N/period form" when the rate string is malformed.
- `ThrottleDeclarationError` with message "unknown rate period" when the rate period is not recognized.
- `ThrottleDeclarationError` with message "scope must be non-empty" when the scope is empty.
- `ThrottleDeclarationError` with message "tier label must be non-empty" when a tier label is empty.
- `ThrottleDeclarationError` with message "tier labels must be unique" when tier labels are duplicated.

## Example Usage

### Attach Policies to Methods

```python
from monitoring_suite.api_limiter import throttled

class DocumentService:
    @throttled("docs:list", "100/hour")
    def list_documents(self) -> list:
        """List all documents."""
        return []

    @throttled("docs:upload", "20/minute", tiers={"free": "5/day", "pro": "1000/hour"})
    def upload(self, file_path: str) -> str:
        """Upload a document."""
        return "doc_id"

    @throttled("docs:delete", "10/hour")
    def delete(self, doc_id: str) -> None:
        """Delete a document."""
        pass
```

### Collect and Inspect Policies

```python
from monitoring_suite.api_limiter import PolicyRegistry

registry = PolicyRegistry()
policies = registry.collect(DocumentService)

print(f"Declared {len(policies)} policies:")
for policy in policies:
    print(f"  Scope: {policy.scope}")
    print(f"  Base rate: {policy.rate.as_rate()}")
    if policy.has_tiers:
        for tier_rate in policy.tier_rates:
            print(f"    {tier_rate.tier}: {tier_rate.rate.as_rate()}")
```

Output:

```
Declared 3 policies:
  Scope: docs:list
  Base rate: 100/hour
  Scope: docs:upload
  Base rate: 20/minute
    free: 5/day
    pro: 1000/hour
  Scope: docs:delete
  Base rate: 10/hour
```

### Adapter Pattern: Build Framework Throttles

```python
from monitoring_suite.api_limiter import PolicyRegistry, RateLimitExceeded
from rest_framework.throttling import SimpleRateThrottle

class ServiceThrottle(SimpleRateThrottle):
    """DRF throttle built from declared policies."""

    scope = None  # Overridden per request

    def allow_request(self, request, view):
        # If the view class has collected policies, use them to set scope.
        if not self.scope:
            registry = PolicyRegistry()
            policies = registry.collect(view.__class__)
            # This is pseudo-code; a real adapter would map view method to policy.
            if policies:
                self.scope = policies[0].scope
        return super().allow_request(request, view)
```

A consuming adapter walks `PolicyRegistry.collect()` and builds throttle classes that implement actual rate-limit enforcement. The decorator ensures policies are valid at import; the adapter ensures throttling is enforced at runtime.

### Tier Overrides

```python
from monitoring_suite.api_limiter import throttled, PolicyRegistry

class APIService:
    @throttled(
        "api:call",
        "100/hour",
        tiers={
            "free": "10/hour",
            "pro": "1000/hour",
            "enterprise": "unlimited"  # Adapter-specific: monitoring_suite.api_limiter stores as a rate string
        }
    )
    def call(self, request_id: str) -> dict:
        return {"status": "ok"}

registry = PolicyRegistry()
policies = registry.collect(APIService)
policy = policies[0]

# Resolve rates by tier
for tier in ["free", "pro", "enterprise"]:
    rate = policy.rate_for(tier)
    print(f"{tier}: {rate.as_rate()}")
```

Output:

```
free: 10/hour
pro: 1000/hour
enterprise: unlimited
```

## See Also

- [Throttle Policy Objects](policy.md) for value object details and validation.
- [Error Types](api_limiter_errors.md) for error handling.
