"""Monitored decorator for automatic metric emission."""

import asyncio
import functools
import inspect
import time
from collections.abc import Callable
from datetime import datetime, timezone
from types import FunctionType
from typing import Any, Optional, cast

from mixin_logging import get_correlation_id

from domain_monitoring.errors.constants import monitoring as const
from domain_monitoring.errors.monitoring_errors import MonitoringDeclarationError
from domain_monitoring.services.constants import metrics as metrics_const
from domain_monitoring.services.metrics.metrics_client import MetricSink
from domain_monitoring.services.metrics.metrics_objects import MetricEvent
from domain_monitoring.services.registry.registry_client import MonitorRegistry


class MonitoredClient:
    """Container for monitored decorator and helper methods."""

    type Labels = tuple[tuple[str, str], ...]
    type LabelsFromResult = Callable[[object], Labels]
    type LabelsFromExc = Callable[[BaseException], Labels]

    @staticmethod
    def monitored[Target](
        event: str,
        sink: Optional[MetricSink] = None,
        labels_from_result: Optional[LabelsFromResult] = None,
        labels_from_exc: Optional[LabelsFromExc] = None,
    ) -> Callable[[Target], Target]:
        """Apply metric tracking to callables and classes."""
        if not event:
            raise MonitoringDeclarationError(const.ERR_MONITORING_EMPTY_EVENT)

        def decorator(target: Target) -> Target:
            """Apply monitoring to target."""
            if inspect.isclass(target):
                return cast(
                    Target,
                    MonitoredClient._monitor_class(
                        target,
                        event,
                        sink,
                        labels_from_result,
                        labels_from_exc,
                    ),
                )
            if callable(target):
                return cast(
                    Target,
                    MonitoredClient._monitor_callable(
                        target,
                        event,
                        sink,
                        labels_from_result,
                        labels_from_exc,
                    ),
                )
            raise MonitoringDeclarationError(const.ERR_MONITORING_INVALID_TARGET)

        return decorator

    @staticmethod
    def _monitor_callable(
        fn: Callable[..., Any],
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[LabelsFromResult],
        labels_from_exc: Optional[LabelsFromExc],
    ) -> Callable[..., Any]:
        """Wrap a callable with monitoring."""
        if asyncio.iscoroutinefunction(fn):
            return MonitoredClient._wrap_async(
                fn, event, sink, labels_from_result, labels_from_exc
            )
        return MonitoredClient._wrap_sync(
            fn, event, sink, labels_from_result, labels_from_exc
        )

    @staticmethod
    def _wrap_sync(
        fn: Callable[..., Any],
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[LabelsFromResult],
        labels_from_exc: Optional[LabelsFromExc],
    ) -> Callable[..., Any]:
        """Wrap synchronous callable."""

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute with metric tracking."""
            started = time.perf_counter()
            actual_sink = MonitoredClient._resolve_sink(sink)
            try:
                result = fn(*args, **kwargs)
            except Exception as error:
                MonitoredClient._emit_failure(
                    actual_sink, event, started, error, labels_from_exc
                )
                raise
            MonitoredClient._emit_success(
                actual_sink, event, started, result, labels_from_result
            )
            return result

        return wrapper

    @staticmethod
    def _wrap_async(
        fn: Callable[..., Any],
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[LabelsFromResult],
        labels_from_exc: Optional[LabelsFromExc],
    ) -> Callable[..., Any]:
        """Wrap asynchronous callable."""

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute async with metric tracking."""
            started = time.perf_counter()
            actual_sink = MonitoredClient._resolve_sink(sink)
            try:
                result = await fn(*args, **kwargs)
            except Exception as error:
                MonitoredClient._emit_failure(
                    actual_sink, event, started, error, labels_from_exc
                )
                raise
            MonitoredClient._emit_success(
                actual_sink, event, started, result, labels_from_result
            )
            return result

        return async_wrapper

    @staticmethod
    def _resolve_sink(sink: Optional[MetricSink]) -> MetricSink:
        """Return the bound sink, falling back to the registry default when unset."""
        if sink is None:
            return MonitorRegistry.get_default_sink()
        return sink

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        """Return milliseconds elapsed since a perf_counter reading."""
        return (time.perf_counter() - started) * 1000

    @staticmethod
    def _emit_success(
        sink: MetricSink,
        event: str,
        started: float,
        result: object,
        labels_from_result: Optional[LabelsFromResult],
    ) -> None:
        """Emit the success event for a completed call."""
        labels = labels_from_result(result) if labels_from_result else ()
        sink.emit(
            MetricEvent.for_success(
                event=event,
                duration_ms=MonitoredClient._elapsed_ms(started),
                occurred_at=datetime.now(timezone.utc).isoformat(),
                labels=MonitoredClient._stamp_correlation_labels(labels),
            )
        )

    @staticmethod
    def _emit_failure(
        sink: MetricSink,
        event: str,
        started: float,
        error: BaseException,
        labels_from_exc: Optional[LabelsFromExc],
    ) -> None:
        """Emit the failure event for a raising call without replacing its exception."""
        try:
            labels = labels_from_exc(error) if labels_from_exc else ()
            sink.emit(
                MetricEvent.for_failure(
                    event=event,
                    duration_ms=MonitoredClient._elapsed_ms(started),
                    occurred_at=datetime.now(timezone.utc).isoformat(),
                    labels=MonitoredClient._stamp_correlation_labels(labels),
                )
            )
        except Exception as recording_error:
            error.add_note(
                f"{metrics_const.NOTE_RECORDING_FAILED}: {recording_error!r}"
            )

    @staticmethod
    def _monitor_class(
        cls: type,
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[LabelsFromResult],
        labels_from_exc: Optional[LabelsFromExc],
    ) -> type:
        """Fan out monitoring to public methods defined on a class."""
        public_methods = MonitoredClient._get_public_methods(cls)

        if not public_methods:
            raise MonitoringDeclarationError(const.ERR_MONITORING_EMPTY_CLASS)

        for method_name in public_methods:
            raw_method = vars(cls)[method_name]
            derived_event = f"{event}.{method_name}"
            if isinstance(raw_method, classmethod):
                wrapped: Any = classmethod(
                    MonitoredClient._monitor_callable(
                        raw_method.__func__,
                        derived_event,
                        sink,
                        labels_from_result,
                        labels_from_exc,
                    )
                )
            elif isinstance(raw_method, staticmethod):
                wrapped = staticmethod(
                    MonitoredClient._monitor_callable(
                        raw_method.__func__,
                        derived_event,
                        sink,
                        labels_from_result,
                        labels_from_exc,
                    )
                )
            else:
                wrapped = MonitoredClient._monitor_callable(
                    raw_method,
                    derived_event,
                    sink,
                    labels_from_result,
                    labels_from_exc,
                )
            setattr(cls, method_name, wrapped)

        return cls

    @staticmethod
    def _get_public_methods(cls: type) -> list[str]:
        """List public functions and method descriptors defined on the class itself."""
        public: list[str] = []
        for name, value in vars(cls).items():
            if name.startswith("_"):
                continue
            if isinstance(value, (FunctionType, classmethod, staticmethod)):
                public.append(name)
        return public

    @staticmethod
    def _stamp_correlation_labels(labels: Labels) -> Labels:
        """Stamp correlation labels from ambient ContextVar; consumer labels win.

        Derives domain lane id as scenario_id/monitoring (if scenario id present).
        Returns merged labels with consumer-provided labels taking precedence.
        """
        scenario_id = get_correlation_id()
        if not scenario_id:
            return labels

        merged = dict(labels)
        merged.setdefault(metrics_const.CORRELATION_LABEL, scenario_id)
        merged.setdefault(
            metrics_const.DOMAIN_CORRELATION_LABEL,
            f"{scenario_id}/{metrics_const.DOMAIN_CORRELATION_LANE}",
        )
        return tuple(sorted(merged.items()))


monitored = MonitoredClient.monitored
