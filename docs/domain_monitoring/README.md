# domain-monitoring

Event monitoring and telemetry for cross-cutting concerns.

## Overview

`domain-monitoring` provides:

- **Metric events**: Each monitored call emits one `MetricEvent` with its outcome, duration and labels
- **Pluggable sinks**: Any object with an `emit(event)` method can receive events
- **Decorator-based**: Apply monitoring with the `@monitored` decorator, to functions, methods, or whole classes
- **Failure-safe recording**: A failing sink never replaces the exception raised by the monitored call

## Quick Start

```python
from domain_monitoring import monitored

# Apply monitoring to a function; with no sink bound it emits to the null sink
@monitored(event="document.created")
def create_document(title: str):
    return {"id": "doc_123", "title": title}
```

Bind a sink once for every unbound `@monitored` declaration:

```python
from domain_monitoring import CollectingSink, MonitorRegistry

MonitorRegistry.set_default_sink(CollectingSink())
```

## Public API

- **`monitored`**: Decorator that emits a metric event for each call
- **`MonitorRegistry`**: Global registry for the default sink
- **`MetricEvent`**: Immutable event with `event`, `outcome`, `duration_ms`, `occurred_at` and `labels`
- **`MetricSink`**: Protocol for sinks (`emit(event) -> None`)
- **`CloudWatchMetricSink`**: Sink that writes events to CloudWatch (needs the `cloudwatch` extra)
- **`CollectingSink`**: In-memory collector for tests and development
- **`NullSink`**: No-op sink (default)
- **`Outcome`**: `SUCCESS` or `FAILURE`
- Monitoring error classes: `MonitoringError`, `MonitoringDeclarationError`

## Features

### Per-Feature Documentation

- **[architecture/flow-trace.md](architecture/flow-trace.md)**: Flow and runtime behaviour
- **[CHANGELOG-history.md](CHANGELOG-history.md)**: Version history before domain-suite consolidation

### Audits and Reviews

- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Basic Event Tracking

```python
from domain_monitoring import CollectingSink, monitored

sink = CollectingSink()

@monitored(event="user.signup", sink=sink)
def signup_user(email: str):
    return {"user_id": "usr_123"}

signup_user("user@example.com")

for event in sink.events:
    print(event.event, event.outcome, round(event.duration_ms, 0) >= 0)
```

**Output (Python 3.12, domain-suite==0.7.0):**
```
user.signup success True
```

### Labels From the Result

`labels_from_result` and `labels_from_exc` return `(key, value)` pairs that are
added to the event. Correlation labels from the ambient correlation id are added
automatically; labels supplied by the callback take precedence.

```python
from domain_monitoring import CollectingSink, monitored

sink = CollectingSink()

def status_labels(result: object) -> tuple[tuple[str, str], ...]:
    if isinstance(result, dict):
        return (("status", str(result["status"])),)
    return ()

@monitored("document.process", sink=sink, labels_from_result=status_labels)
def process(doc_id: str) -> dict[str, str]:
    return {"status": "completed"}

process("doc_1")
print(sink.events[0].labels)
```

### Recording Events Directly

```python
from domain_monitoring import CollectingSink, MetricEvent

sink = CollectingSink()
event = MetricEvent.for_success(
    "document.processed",
    125.0,
    "2026-10-18T12:00:00+00:00",
    (("pages", "50"),),
)
sink.emit(event)
print(sink.events[0].labels)
```

## Integration with domain-aspects

The `Monitored` aspect applies the same behaviour inside `@aspects(...)` and
accepts the same `labels_from_result` and `labels_from_exc` callbacks.

## Next Steps

- Read the [main domain-suite README](../../README.md) for installation and examples
- Explore [architecture/flow-trace.md](architecture/flow-trace.md) for the runtime sequence
- Implement a sink for your metrics backend with an `emit(event)` method
