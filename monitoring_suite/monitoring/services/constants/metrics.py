"""Metric event validation and CloudWatch configuration constants. Imported as const."""

from __future__ import annotations

from datetime import datetime
from typing import Final, Literal, TypedDict

"""Metric event validation error messages."""

ERR_METRIC_EVENT_EMPTY: Final[str] = "event must be non-empty"
ERR_METRIC_DURATION_NEGATIVE: Final[str] = "duration_ms must be non-negative"
ERR_METRIC_OCCURRED_AT_EMPTY: Final[str] = "occurred_at must be non-empty"


"""CloudWatch sink configuration."""

DEFAULT_CLOUDWATCH_NAMESPACE: Final[str] = "monitoring-suite"
CLOUDWATCH_METRIC_UNIT: Final[str] = "Milliseconds"
CLOUDWATCH_DIMENSION_OUTCOME: Final[str] = "Outcome"


"""Correlation labels and unit conversion."""

LABEL_CORRELATION_ID: Final[str] = "correlation_id"
LABEL_DOMAIN_CORRELATION_ID: Final[str] = "domain_correlation_id"
DOMAIN_LANE_SUFFIX: Final[str] = "/monitoring"
MILLISECONDS_PER_SECOND: Final[int] = 1000


"""Separators and format pieces."""

EVENT_SEPARATOR: Final[str] = "."


"""Decorator markers and member-name conventions."""

PRIVATE_PREFIX: Final[str] = "_"
ATTR_BASES: Final[str] = "__bases__"


"""CloudWatch request keys and service name."""

CLOUDWATCH_SERVICE_NAME: Final[str] = "cloudwatch"
CLOUDWATCH_KEY_METRIC_NAME: Final[Literal["MetricName"]] = "MetricName"
CLOUDWATCH_KEY_VALUE: Final[Literal["Value"]] = "Value"
CLOUDWATCH_KEY_UNIT: Final[Literal["Unit"]] = "Unit"
CLOUDWATCH_KEY_TIMESTAMP: Final[Literal["Timestamp"]] = "Timestamp"
CLOUDWATCH_KEY_DIMENSIONS: Final[Literal["Dimensions"]] = "Dimensions"
CLOUDWATCH_KEY_NAME: Final[str] = "Name"


"""Enumeration member values."""

OUTCOME_SUCCESS: Final[str] = "success"
OUTCOME_FAILURE: Final[str] = "failure"


"""Typed dictionaries of the CloudWatch request."""


class MetricDatapoint(TypedDict, total=False):
    """Metric data point for AWS CloudWatch put_metric_data API."""

    MetricName: str
    Value: float
    Unit: str
    Timestamp: datetime
    Dimensions: list[dict[str, str]]
