"""Metric sink protocol and event collection."""

from monitoring_suite.monitoring.services.metrics.metrics_client import (
    CollectingSink,
    MetricSink,
    NullSink,
)
from monitoring_suite.monitoring.services.metrics.metrics_objects import MetricEvent

__all__ = ["CollectingSink", "MetricEvent", "MetricSink", "NullSink"]
