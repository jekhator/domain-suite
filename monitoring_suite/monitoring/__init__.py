"""Domain monitoring library."""

from monitoring_suite.monitoring.config._version import __version__
from monitoring_suite.monitoring.decorators.monitored.monitored_client import monitored
from monitoring_suite.monitoring.errors.monitoring_errors import MonitoringDeclarationError, MonitoringError
from monitoring_suite.monitoring.services.metrics.metrics_client import CollectingSink, MetricSink, NullSink
from monitoring_suite.monitoring.services.metrics.metrics_objects import MetricEvent, Outcome
from monitoring_suite.monitoring.services.registry.registry_client import MonitorRegistry

try:
    from monitoring_suite.monitoring.services.metrics.cloudwatch_sink import CloudWatchMetricSink
except ImportError:  # pragma: no cover
    CloudWatchMetricSink = None  # type: ignore

__all__ = [
    "__version__", "CloudWatchMetricSink", "CollectingSink", "MetricEvent", "MetricSink",
    "MonitorRegistry", "MonitoringDeclarationError", "MonitoringError", "NullSink", "Outcome", "monitored"
]
