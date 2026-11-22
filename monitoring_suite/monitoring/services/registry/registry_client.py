"""Global monitoring registry for sink resolution."""

from typing import Optional

from monitoring_suite.monitoring.services.metrics.metrics_client import MetricSink, NullSink


class MonitorRegistry:
    """Global registry for metric sink binding."""

    _default_sink: Optional[MetricSink] = None

    @classmethod
    def set_default_sink(cls, sink: MetricSink) -> None:
        """Set the default sink for all unbound monitoring."""
        cls._default_sink = sink

    @classmethod
    def get_default_sink(cls) -> MetricSink:
        """Get the current default sink, or NullSink if unset."""
        return cls._default_sink or NullSink()

    @classmethod
    def clear_default_sink(cls) -> None:
        """Clear the default sink."""
        cls._default_sink = None
