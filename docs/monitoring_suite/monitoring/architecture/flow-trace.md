# monitoring_suite.monitoring: Flow-Trace

## Overview

Automatic metric emission via `@monitored` decorator. Wraps callables and classes, emitting `MetricEvent` (success or failure) to a configurable `MetricSink` after each call. Default sink is `NullSink` (no-op); `MonitorRegistry` provides global default-sink binding. Preserves sync/async dispatch.

## Entry Unit

`@monitored(event="user.fetch", sink=None)` decorator ──▶ `MetricEvent` emission.

## Flow-Trace Diagram

```
① CONSTRUCT MetricEvent [FROZEN,slots]
   event: str  ← event name (e.g., "user.fetch")
   outcome: Outcome  ← Outcome.SUCCESS | Outcome.FAILURE
   duration_ms: float  ← elapsed time in milliseconds
   occurred_at: str  ← ISO 8601 timestamp
   labels: tuple[tuple[str, str], ...] = ()  ← optional key-value pairs

   Outcome ← StrEnum: SUCCESS="success", FAILURE="failure"

② CONSTRUCT MetricSink [PROTOCOL]
   MetricSink.emit(event: MetricEvent) -> None  ← abstract method

   Implementations:
   ├─ NullSink()  ← no-op, default
   ├─ CollectingSink()  ← in-memory list for testing/dev
   └─ custom sinks (e.g., CloudWatch, DataDog)

③ DECORATE @monitored
   @monitored(event="user.fetch", sink=None)  ──▶ monitored(event, sink)
      ├─ decorator(target)
      │  ├─ isclass(target)?
      │  │  ├─ YES ──▶ _monitor_class(target, event, sink)
      │  │  │  ├─ _get_public_methods(cls)  ← skip _-prefixed, inherited, special
      │  │  │  ├─ for method_name in public_methods
      │  │  │  │  ├─ derived_event = f"{event}.{method_name}"  ← fan-out event
      │  │  │  │  ├─ monitored_method = _monitor_callable(original_method, derived_event, sink)
      │  │  │  │  └─ setattr(cls, method_name, monitored_method)
      │  │  │  └─ returns cls
      │  │  └─ NO (callable) ──▶ _monitor_callable(target, event, sink)
      │  │     ├─ asyncio.iscoroutinefunction(fn)?
      │  │     │  ├─ YES ──▶ _wrap_async(fn, event, sink)
      │  │     │  └─ NO  ──▶ _wrap_sync(fn, event, sink)
      │  │     └─ returns wrapped callable
      └─ returns wrapped target

④ RUNTIME (sync path) ──▶ wrapper(*args, **kwargs)
      ├─ start_time = datetime.now(timezone.utc)
      ├─ actual_sink = sink or MonitorRegistry.get_default_sink()  ← resolve sink
      ├─ try:
      │  ├─ result = fn(*args, **kwargs)  ← execute
      │  ├─ end_time = datetime.now(timezone.utc)
      │  ├─ duration_ms = (end_time - start_time).total_seconds() * 1000
      │  ├─ metric_event = MetricEvent.for_success(event=event, duration_ms=duration_ms, occurred_at=end_time.isoformat())
      │  ├─ actual_sink.emit(metric_event)  ← send to sink
      │  └─ return result
      └─ except Exception:
         ├─ end_time = datetime.now(timezone.utc)
         ├─ duration_ms = (end_time - start_time).total_seconds() * 1000
         ├─ metric_event = MetricEvent.for_failure(event=event, duration_ms=duration_ms, occurred_at=end_time.isoformat())
         ├─ actual_sink.emit(metric_event)  ← send to sink
         └─ raise  ← exception propagates

⑤ RUNTIME (async path) ──▶ async async_wrapper(*args, **kwargs)
      ├─ start_time = datetime.now(timezone.utc)
      ├─ actual_sink = sink or MonitorRegistry.get_default_sink()
      ├─ try:
      │  ├─ result = await fn(*args, **kwargs)  ← execute async
      │  ├─ end_time = datetime.now(timezone.utc)
      │  ├─ duration_ms = (end_time - start_time).total_seconds() * 1000
      │  ├─ metric_event = MetricEvent.for_success(...)
      │  ├─ actual_sink.emit(metric_event)
      │  └─ return result
      └─ except Exception:
         ├─ [same as sync failure branch]
         └─ raise

⑥ REGISTRY BINDING
   MonitorRegistry.set_default_sink(sink)  ← global default for @monitored(event, sink=None)
   MonitorRegistry.get_default_sink()  ← returns _default_sink or NullSink()
   MonitorRegistry.clear_default_sink()  ← reset

REAL OUTPUT (success):
   EMITTED MetricEvent: user.fetch
     outcome: success
     duration_ms: 0.0
     occurred_at: 2026-07-11T19:56:28.141743+00:00

REAL OUTPUT (failure):
   EMITTED MetricEvent: user.delete
     outcome: failure
     is_failure: True
     duration_ms: 0.0
```

## Key Constants

- `Outcome.SUCCESS` = "success"
- `Outcome.FAILURE` = "failure"
- `ERR_MONITORING_INVALID_TARGET` = "monitoring target must be callable or class"
- `ERR_MONITORING_EMPTY_CLASS` = "class has no public methods to monitor"

## Core Classes

- `MetricEvent` ← frozen slots; event, outcome, duration_ms, occurred_at, labels; __hash__; for_success(), for_failure() classmethods; is_failure property
- `Outcome` ← StrEnum; SUCCESS, FAILURE
- `MetricSink` ← Protocol; emit(event: MetricEvent) -> None
- `NullSink` ← no-op implementation
- `CollectingSink` ← in-memory list; emit(), events property, clear()
- `MonitorRegistry` ← static methods; set_default_sink(), get_default_sink(), clear_default_sink()

## Design Notes

- Metrics are emitted even on exception (no swallow; exception propagates after emit)
- Default NullSink ensures @monitored is safe without explicit sink binding
- Class decoration fans out: event becomes "event.method_name" for each method
- Duration includes exception-handling time (start to end, always)
