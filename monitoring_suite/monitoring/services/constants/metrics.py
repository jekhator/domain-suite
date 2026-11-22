"""Metric event validation and CloudWatch configuration constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Metric event validation error messages."""

ERR_METRIC_EVENT_EMPTY: Final[str] = "event must be non-empty"
ERR_METRIC_DURATION_NEGATIVE: Final[str] = "duration_ms must be non-negative"
ERR_METRIC_OCCURRED_AT_EMPTY: Final[str] = "occurred_at must be non-empty"


"""CloudWatch sink configuration."""

DEFAULT_CLOUDWATCH_NAMESPACE: Final[str] = "monitoring-suite"
CLOUDWATCH_METRIC_UNIT: Final[str] = "Milliseconds"
CLOUDWATCH_DIMENSION_OUTCOME: Final[str] = "Outcome"
