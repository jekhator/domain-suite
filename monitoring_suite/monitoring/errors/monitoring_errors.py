"""Monitoring domain errors. Imported as const.ERR_*."""

from monitoring_suite.errors import DomainError
from monitoring_suite.monitoring.errors.constants import monitoring as const


class MonitoringError(DomainError):
    """Monitoring operation failed."""

    domain = const.DOMAIN_MONITORING
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_MONITORING_FAILED


class MonitoringDeclarationError(DomainError):
    """Invalid decorator target or declaration."""

    domain = const.DOMAIN_MONITORING
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_MONITORING_INVALID_TARGET
