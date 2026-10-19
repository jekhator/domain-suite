"""Monitoring error messages. Imported as const."""

from typing import Final

# Monitoring failures.
ERR_MONITORING_FAILED: Final = "Monitoring operation failed"

# Invalid decorator targets.
ERR_MONITORING_INVALID_TARGET: Final = (
    "Invalid monitoring target: must be a callable or class"
)

# Empty class decoration.
ERR_MONITORING_EMPTY_CLASS: Final = "Cannot monitor class with no public methods"

# Empty event name.
ERR_MONITORING_EMPTY_EVENT: Final = "Monitoring event name must be non-empty"

# Missing optional dependencies.
ERR_MONITORING_BOTO3_MISSING: Final = (
    "CloudWatch sink requires boto3; install with: pip install domain-suite[cloudwatch]"
)
