# domain_monitoring: Flow-Trace

## Overview

Automatic metric emission through the `@monitored` decorator. The decorator
wraps a callable, or every public method defined on a class, and emits one
`MetricEvent` per call to a `MetricSink`: a success event when the call returns,
or a failure event when it raises. The call's own result or exception is
returned or re-raised unchanged. Sync and async callables keep their dispatch.

## Entry Unit

`@monitored(event="user.fetch", sink=None, labels_from_result=None, labels_from_exc=None)`
decorator, applied to a callable or a class.

## Flow-Trace Diagram

```
1. CONSTRUCT MetricEvent [FROZEN, slots]
   event: str                 event name, for example "user.fetch"
   outcome: Outcome           Outcome.SUCCESS or Outcome.FAILURE
   duration_ms: float         elapsed milliseconds (monotonic clock)
   occurred_at: str           ISO 8601 timestamp of the end of the call
   labels: tuple[tuple[str, str], ...] = ()

2. MetricSink [PROTOCOL]
   emit(event: MetricEvent) -> None

   Implementations:
   - NullSink()          no-op, used when no sink is bound
   - CollectingSink()    in-memory list for tests and development
   - CloudWatchMetricSink()   boto3 put_metric_data (cloudwatch extra)

3. DECORATE @monitored
   monitored(event, sink, labels_from_result, labels_from_exc)
   - empty event name -> MonitoringDeclarationError (at declaration)
   - decorator(target)
     - class?      -> _monitor_class: for each public function or method
                      defined on the class itself, derived event is
                      "<event>.<method>"; classmethods and staticmethods keep
                      their descriptor type
     - callable?   -> _monitor_callable: coroutine function -> async wrapper,
                      otherwise sync wrapper
     - anything else -> MonitoringDeclarationError

4. RUNTIME (sync) wrapper(*args, **kwargs)
   - started = perf_counter()
   - actual_sink = sink, or MonitorRegistry.get_default_sink() when sink is None
   - try:
       result = fn(*args, **kwargs)
     except Exception as error:
       _emit_failure(...)   labels_from_exc and the failure event are built here;
                            a failure while recording is attached to `error` as a
                            note, so the original exception is re-raised
       raise
   - _emit_success(...)     labels_from_result and the success event are built here;
                            a sink error propagates to the caller
   - return result

5. RUNTIME (async) async_wrapper(*args, **kwargs)
   - same sequence, with `await fn(*args, **kwargs)` in the try block

6. REGISTRY BINDING
   MonitorRegistry.set_default_sink(sink)   global default for sink=None
   MonitorRegistry.get_default_sink()       returns the bound sink (identity check),
                                            or the shared NullSink when unset
   MonitorRegistry.clear_default_sink()     resets to unset

REAL OUTPUT (success and failure):
   EMITTED MetricEvent: user.fetch
     outcome: success
     is_failure: False
     duration_ms >= 0: True
     occurred_at: 2026-10-19T03:15:56.760111+00:00
   EMITTED MetricEvent: user.delete
     outcome: failure
     is_failure: True
     duration_ms >= 0: True
     occurred_at: 2026-10-19T03:15:56.760148+00:00
```

## Key Constants

- `Outcome.SUCCESS` = "success"
- `Outcome.FAILURE` = "failure"
- `ERR_MONITORING_INVALID_TARGET` = "Invalid monitoring target: must be a callable or class"
- `ERR_MONITORING_EMPTY_CLASS` = "Cannot monitor class with no public methods"
- `ERR_MONITORING_EMPTY_EVENT` = "Monitoring event name must be non-empty"

## Core Classes

- `MetricEvent`: frozen slots dataclass; `for_success()` and `for_failure()` classmethods; `is_failure` property
- `Outcome`: StrEnum with `SUCCESS` and `FAILURE`
- `MetricSink`: Protocol with `emit(event)`
- `NullSink`: no-op implementation
- `CollectingSink`: in-memory list with `emit()`, an `events` copy property and `clear()`
- `MonitorRegistry`: class methods `set_default_sink()`, `get_default_sink()`, `clear_default_sink()`

## Design Notes

- Failures are recorded and the original exception propagates unchanged.
- Duration is measured with a monotonic clock, so a wall-clock change cannot produce a negative duration.
- Default NullSink keeps `@monitored` safe without an explicit sink binding.
- Class decoration covers functions and method descriptors defined on the class itself. Inherited methods are not wrapped; an override is.
- Correlation labels from the ambient correlation id are added unless the callback supplies the same key.
