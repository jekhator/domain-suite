"""Domain monitoring library."""

from domain_monitoring.config._version import __version__
from domain_monitoring.decorators.monitored.monitored_client import monitored
from domain_monitoring.errors.monitoring_errors import (
    MonitoringDeclarationError,
    MonitoringError,
)
from domain_monitoring.services.metrics.cloudwatch_sink import CloudWatchMetricSink
from domain_monitoring.services.metrics.metrics_client import (
    CollectingSink,
    MetricSink,
    NullSink,
)
from domain_monitoring.services.metrics.metrics_objects import MetricEvent, Outcome
from domain_monitoring.services.registry.registry_client import MonitorRegistry

__all__ = [
    "__version__",
    "CloudWatchMetricSink",
    "CollectingSink",
    "MetricEvent",
    "MetricSink",
    "MonitorRegistry",
    "MonitoringDeclarationError",
    "MonitoringError",
    "NullSink",
    "Outcome",
    "monitored",
]
