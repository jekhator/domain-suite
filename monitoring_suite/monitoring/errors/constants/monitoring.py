"""Monitoring error messages. Imported as const."""

from typing import Final

"""Monitoring failures."""

ERR_MONITORING_FAILED: Final[str] = "Monitoring operation failed"

"""Invalid decorator targets."""

ERR_MONITORING_INVALID_TARGET: Final[str] = "Invalid monitoring target: must be a callable or class"

"""Empty class decoration."""

ERR_MONITORING_EMPTY_CLASS: Final[str] = "Cannot monitor class with no public methods"

"""Missing optional dependencies."""

ERR_MONITORING_BOTO3_MISSING: Final[str] = (
    "CloudWatch sink requires boto3; install with: pip install monitoring-suite[cloudwatch]"
)


"""Error class contract values: domain, codes and HTTP statuses."""

DOMAIN_MONITORING: Final[str] = "monitoring"
HTTP_STATUS_INTERNAL_SERVER_ERROR: Final[int] = 500
