"""Retrieval domain errors. Imported as const.ERR_*."""

from monitoring_suite.errors import DomainError
from monitoring_suite.rag.errors.constants import retrieval as const


class RetrievalError(DomainError):
    """Retrieval operation failed."""

    domain = const.DOMAIN_RETRIEVAL
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_RETRIEVAL_FAILED


class RetrievalDeclarationError(DomainError):
    """Invalid decorator target or declaration."""

    domain = const.DOMAIN_RETRIEVAL
    http_status = const.HTTP_STATUS_INTERNAL_SERVER_ERROR
    retryable = False
    default_message = const.ERR_RETRIEVAL_INVALID_TARGET
