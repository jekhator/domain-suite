"""Metric event validation and CloudWatch configuration constants. Imported as const."""

from __future__ import annotations

from typing import Final

ERR_METRIC_EVENT_EMPTY: Final = "event must be non-empty"
ERR_METRIC_DURATION_NEGATIVE: Final = "duration_ms must be non-negative"
ERR_METRIC_OCCURRED_AT_EMPTY: Final = "occurred_at must be non-empty"

NOTE_RECORDING_FAILED: Final = "metric sink failed while recording a failed call"

CORRELATION_LABEL: Final = "correlation_id"
DOMAIN_CORRELATION_LABEL: Final = "domain_correlation_id"
DOMAIN_CORRELATION_LANE: Final = "monitoring"

DEFAULT_CLOUDWATCH_NAMESPACE: Final = "domain-monitoring"
CLOUDWATCH_METRIC_UNIT: Final = "Milliseconds"
CLOUDWATCH_DIMENSION_OUTCOME: Final = "Outcome"
