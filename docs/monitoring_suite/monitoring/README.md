# monitoring_suite.monitoring

Event monitoring and telemetry for cross-cutting concerns.

## Overview

`monitoring_suite.monitoring` provides:

- **Event registry**: Central registry for domain events
- **Metric collection**: Track events with outcomes and latency
- **Pluggable sinks**: Output metrics to external systems (CloudWatch, Prometheus, etc.)
- **Decorator-based**: Apply monitoring with `@monitored` decorator

## Quick Start

```python
from monitoring_suite.monitoring import monitored, MonitorRegistry

registry = MonitorRegistry()

# Apply monitoring to functions
@monitored(event="document.created")
def create_document(title: str):
    return {"id": "doc_123", "title": title}

# The decorator automatically tracks:
# - Success/failure outcomes
# - Latency (milliseconds)
# - Event name and metadata
```

## Public API

- **`monitored`**: Decorator to track function execution as domain events
- **`MonitorRegistry`**: Central registry for metrics and sinks
- **`MetricEvent`**: Domain event with metadata (name, outcome, latency, etc.)
- **`MetricSink`**: Abstract sink interface for outputting metrics
- **`CollectingSink`**: In-memory collector for testing
- **`NullSink`**: No-op sink (default)
- **`Outcome`**: Success/failure/error outcome enum
- Monitoring error classes: `MonitoringError`, `MonitoringDeclarationError`

## Features

### Per-Feature Documentation

Detailed documentation for event monitoring:

- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before monitoring-suite consolidation

### Security & Code Quality

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Basic Event Tracking

```python
from monitoring_suite.monitoring import monitored, MonitorRegistry, CollectingSink

registry = MonitorRegistry()
sink = CollectingSink()
registry.set_default_sink(sink)

@monitored(event="user.signup")
def signup_user(email: str):
    return {"user_id": "usr_123"}

# Call the function
signup_user("user@example.com")

# Inspect events
for event in sink.events:
    print(f"Event: {event.event_name}, Outcome: {event.outcome}, Latency: {event.latency_ms}ms")
```

### Custom Metrics

```python
from monitoring_suite.monitoring import MonitorRegistry, MetricEvent, Outcome

registry = MonitorRegistry()

# Manually emit events (lower-level API)
event = MetricEvent(
    event_name="document.processed",
    outcome=Outcome.SUCCESS,
    latency_ms=125,
    context={"doc_id": "doc_123", "pages": 50}
)
registry.log_event(event)
```

## Integration with monitoring_suite.aspects

Use the `@Logged` aspect for composable event logging:

```python
from monitoring_suite.aspects import aspects, Logged

@aspects(
    Logged(event="document.created"),
)
def create_document(title: str):
    pass
```

## Next Steps

- Read the [main monitoring-suite README](../../README.md) for installation and examples
- Check [CHANGELOG-history.md](CHANGELOG-history.md) for version history before consolidation
- Explore event sink implementations for your observability platform
