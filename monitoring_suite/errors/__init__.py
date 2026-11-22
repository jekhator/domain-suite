"""Typed domain error hierarchy with wrapping and chaining for Python services."""

from monitoring_suite.errors.config._version import __version__
from monitoring_suite.errors.decorators.wrap_errors.wrap_errors_client import WrapErrorsClient, wrap_errors
from monitoring_suite.errors.domains.domain_error.domain_error import DomainError
from monitoring_suite.errors.services.chain.chain_client import ErrorChain
from monitoring_suite.errors.services.chain.chain_objects import ChainLink, ChainVia, DomainClassifier, DomainCrossing

__all__ = [
    "ChainLink", "ChainVia", "DomainClassifier", "DomainCrossing",
    "DomainError", "ErrorChain", "WrapErrorsClient", "__version__", "wrap_errors"
]
