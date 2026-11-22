"""Metric event validation and CloudWatch configuration constants. Imported as const."""

from __future__ import annotations

from typing import Final

ERR_METRIC_EVENT_EMPTY: Final = "event must be non-empty"
ERR_METRIC_DURATION_NEGATIVE: Final = "duration_ms must be non-negative"
ERR_METRIC_OCCURRED_AT_EMPTY: Final = "occurred_at must be non-empty"

DEFAULT_CLOUDWATCH_NAMESPACE: Final = "monitoring-suite"
CLOUDWATCH_METRIC_UNIT: Final = "Milliseconds"
CLOUDWATCH_DIMENSION_OUTCOME: Final = "Outcome"
