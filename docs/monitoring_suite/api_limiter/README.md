# monitoring_suite.api_limiter

Request rate limiting and quota enforcement for Python services.

## Overview

`monitoring_suite.api_limiter` provides:

- **Throttle policies**: Declarative rate-limit definitions (e.g., 100 requests/hour)
- **Tier-based rate limits**: Different limits per caller or usage tier
- **Quota enforcement**: Decorator-based throttle application
- **Flexible backends**: Pluggable storage (in-memory, Redis, etc.)

## Quick Start

```python
from monitoring_suite.api_limiter import throttled, PolicyRegistry

# Define rate limit policy
policy_registry = PolicyRegistry()
policy_registry.add_policy("api.documents", {
    "free": "10/hour",
    "starter": "100/hour",
    "pro": "1000/hour",
})

# Enforce via decorator
@throttled(scope="api.documents", rate="100/hour")
def create_document(title: str):
    return {"id": "doc_123", "title": title}
```

## Public API

- **`throttled`**: Decorator to enforce rate limits on functions
- **`PolicyRegistry`**: Central policy storage and lookup
- **`ThrottlePolicy`**: Rate limit policy definition
- **`RateLimit`**: Per-scope rate limit tracking
- **`TierRate`**: Tier-specific rate configurations
- **`Period`**: Time period (hourly, daily, etc.)
- **`RateLimitExceeded`**: Exception raised when limit is exceeded
- Throttle error classes: `ThrottleError`, `ThrottleDeclarationError`

## Features

### Per-Feature Documentation

Detailed documentation for each feature:

- **[policy.md](apps/policy.md)**: Policy definition and tier-based configuration
- **[throttled.md](apps/throttled.md)**: Throttle decorator and enforcement
- **[api_limiter_errors.md](apps/api_limiter_errors.md)**: Exception hierarchy

### Architecture & Design

- **[diagrams.md](apps/diagrams.md)**: Visual guides to throttle policy and storage
- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before monitoring-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Tier-Based Rate Limiting

```python
from monitoring_suite.api_limiter import PolicyRegistry, ThrottlePolicy, TierRate, Period

policy_registry = PolicyRegistry()

# Define tier-based limits
policy = ThrottlePolicy(
    scope="api.documents",
    tiers={
        "free": TierRate(limit=10, period=Period.HOURLY),
        "pro": TierRate(limit=1000, period=Period.HOURLY),
    }
)
policy_registry.add_policy("api.documents", policy)
```

### Per-Tenant Rate Limiting

```python
@throttled(scope="api.documents.{tenant_id}", rate="100/hour")
def create_document(tenant_id: str, title: str):
    return {"id": "doc_123", "title": title}
```

## Integration with monitoring_suite.aspects

Use the `@Throttled` aspect for composable rate limiting:

```python
from monitoring_suite.aspects import aspects, Throttled

@aspects(
    Throttled(scope="api.documents", rate="100/hour"),
)
def create_document(title: str):
    pass
```

## Next Steps

- Read the [main monitoring-suite README](../../README.md) for installation and examples
- Choose a feature from the list above and read its detailed documentation
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
