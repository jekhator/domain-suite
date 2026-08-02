"""Tests for CloudWatchMetricSink."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from domain_monitoring.services.metrics.metrics_objects import MetricEvent


class TestCloudWatchMetricSink:
    """CloudWatchMetricSink tests."""

    def test_cloudwatch_sink_emit_success(self) -> None:
        """CloudWatchMetricSink emits success metric to mocked CloudWatch."""
        mock_boto3 = MagicMock()
        mock_cw = MagicMock()
        mock_boto3.client.return_value = mock_cw

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            from domain_monitoring.services.metrics.cloudwatch_sink import (
                CloudWatchMetricSink,
            )

            sink = CloudWatchMetricSink(namespace="test-ns")
            now = datetime.now(timezone.utc)
            event = MetricEvent.for_success(
                event="test.operation",
                duration_ms=123.45,
                occurred_at=now.isoformat(),
                labels=(("env", "test"), ("version", "1.0")),
            )

            sink.emit(event)

            mock_cw.put_metric_data.assert_called_once()
            call_args = mock_cw.put_metric_data.call_args
            assert call_args.kwargs["Namespace"] == "test-ns"
            assert len(call_args.kwargs["MetricData"]) == 1
            metric = call_args.kwargs["MetricData"][0]
            assert metric["MetricName"] == "test.operation"
            assert metric["Value"] == 123.45
            assert metric["Unit"] == "Milliseconds"
            assert metric["Timestamp"] == now
            dimensions = {d["Name"]: d["Value"] for d in metric["Dimensions"]}
            assert dimensions["Outcome"] == "success"
            assert dimensions["env"] == "test"
            assert dimensions["version"] == "1.0"

    def test_cloudwatch_sink_emit_failure(self) -> None:
        """CloudWatchMetricSink emits failure metric with outcome dimension."""
        mock_boto3 = MagicMock()
        mock_cw = MagicMock()
        mock_boto3.client.return_value = mock_cw

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            from domain_monitoring.services.metrics.cloudwatch_sink import (
                CloudWatchMetricSink,
            )

            sink = CloudWatchMetricSink(namespace="prod-ns")
            now = datetime.now(timezone.utc)
            event = MetricEvent.for_failure(
                event="test.failed_operation",
                duration_ms=456.78,
                occurred_at=now.isoformat(),
                labels=(("error_type", "ValueError"),),
            )

            sink.emit(event)

            call_args = mock_cw.put_metric_data.call_args
            metric = call_args.kwargs["MetricData"][0]
            assert metric["MetricName"] == "test.failed_operation"
            assert metric["Value"] == 456.78
            dimensions = {d["Name"]: d["Value"] for d in metric["Dimensions"]}
            assert dimensions["Outcome"] == "failure"
            assert dimensions["error_type"] == "ValueError"

    def test_cloudwatch_sink_no_labels(self) -> None:
        """CloudWatchMetricSink handles events with no labels."""
        mock_boto3 = MagicMock()
        mock_cw = MagicMock()
        mock_boto3.client.return_value = mock_cw

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            from domain_monitoring.services.metrics.cloudwatch_sink import (
                CloudWatchMetricSink,
            )

            sink = CloudWatchMetricSink()
            now = datetime.now(timezone.utc)
            event = MetricEvent.for_success(
                event="test.no_labels",
                duration_ms=100.0,
                occurred_at=now.isoformat(),
            )

            sink.emit(event)

            call_args = mock_cw.put_metric_data.call_args
            metric = call_args.kwargs["MetricData"][0]
            dimensions = {d["Name"]: d["Value"] for d in metric["Dimensions"]}
            assert "Outcome" in dimensions
            assert len(dimensions) == 1

    def test_cloudwatch_sink_missing_boto3(self) -> None:
        """CloudWatchMetricSink raises clear error when boto3 missing."""
        from domain_monitoring.services.metrics.cloudwatch_sink import (
            CloudWatchMetricSink,
        )

        def init_no_boto3(self, namespace: str = "domain-monitoring") -> None:
            try:
                raise ImportError("No module named 'boto3'")
            except ImportError as error:
                from domain_monitoring.errors.constants import (
                    monitoring as const,
                )

                raise ImportError(const.ERR_MONITORING_BOTO3_MISSING) from error

        with patch.object(CloudWatchMetricSink, "__init__", init_no_boto3):
            with pytest.raises(ImportError, match="CloudWatch sink requires boto3"):
                CloudWatchMetricSink()

    def test_cloudwatch_sink_default_namespace(self) -> None:
        """CloudWatchMetricSink uses default namespace if not specified."""
        mock_boto3 = MagicMock()
        mock_cw = MagicMock()
        mock_boto3.client.return_value = mock_cw

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            from domain_monitoring.services.metrics.cloudwatch_sink import (
                CloudWatchMetricSink,
            )

            sink = CloudWatchMetricSink()
            assert sink.namespace == "domain-monitoring"
