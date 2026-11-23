"""CloudWatch metric sink for production metric emission."""

from __future__ import annotations

from datetime import datetime

from monitoring_suite.monitoring.errors.constants import monitoring as const
from monitoring_suite.monitoring.services.constants import metrics as metrics_const
from monitoring_suite.monitoring.services.metrics import metrics_objects as objs


class CloudWatchMetricSink:
    """Emit MetricEvent to AWS CloudWatch via boto3."""

    def __init__(self, namespace: str = metrics_const.DEFAULT_CLOUDWATCH_NAMESPACE) -> None:
        """
        Initialize CloudWatch sink.

        Args:
            namespace:
                CloudWatch namespace for metrics.
        """
        try:
            import boto3
        except ImportError as error:  # pragma: no cover
            raise ImportError(const.ERR_MONITORING_BOTO3_MISSING) from error

        self.namespace = namespace
        self._cloudwatch = boto3.client(metrics_const.CLOUDWATCH_SERVICE_NAME)

    def emit(self, event: objs.MetricEvent) -> None:
        """
        Emit metric event to CloudWatch.

        Args:
            event:
                MetricEvent with outcome, duration, and labels.
        """
        timestamp = datetime.fromisoformat(event.occurred_at)
        dimensions = self._build_dimensions(event)
        metric_point: metrics_const.MetricDatapoint = {
            metrics_const.CLOUDWATCH_KEY_METRIC_NAME: event.event,
            metrics_const.CLOUDWATCH_KEY_VALUE: event.duration_ms,
            metrics_const.CLOUDWATCH_KEY_UNIT: metrics_const.CLOUDWATCH_METRIC_UNIT,
            metrics_const.CLOUDWATCH_KEY_TIMESTAMP: timestamp, metrics_const.CLOUDWATCH_KEY_DIMENSIONS: dimensions
        }
        self._cloudwatch.put_metric_data(Namespace=self.namespace, MetricData=[metric_point])

    @staticmethod
    def _build_dimensions(event: objs.MetricEvent) -> list[dict[str, str]]:
        """
        Build CloudWatch dimensions from metric event labels and outcome.

        Args:
            event:
                MetricEvent with labels and outcome.

        Returns:
            List of dimension dicts for CloudWatch.
        """
        dimensions: list[dict[str, str]] = [
            {
                metrics_const.CLOUDWATCH_KEY_NAME: metrics_const.CLOUDWATCH_DIMENSION_OUTCOME,
                metrics_const.CLOUDWATCH_KEY_VALUE: event.outcome.value
            }
        ]

        for label_key, label_value in event.labels:
            dimensions.append(
                {metrics_const.CLOUDWATCH_KEY_NAME: label_key, metrics_const.CLOUDWATCH_KEY_VALUE: label_value}
            )

        return dimensions
