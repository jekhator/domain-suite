"""Cross-cutting security concerns: authorization, tenancy, secrets, context management."""

from monitoring_suite.security.config._version import __version__
from monitoring_suite.security.context.security_context.security_context_client import (
    SecurityContextManager,
)
from monitoring_suite.security.context.security_context.security_context_objects import (
    Principal,
    SecurityContext,
)
from monitoring_suite.security.decorators.requires.requires_client import requires
from monitoring_suite.security.decorators.tenant_scoped.tenant_scoped_client import (
    tenant_scoped,
)
from monitoring_suite.security.errors.security_errors import (
    AuthzError,
    SecretError,
    SecurityDeclarationError,
    SecurityError,
    TenancyError,
)
from monitoring_suite.security.services.authz.authz_client import Authorizer
from monitoring_suite.security.services.authz.authz_objects import (
    Permission,
    PolicyDecision,
)
from monitoring_suite.security.services.secrets.secrets_client import SecretRef
from monitoring_suite.security.services.secrets.secrets_objects import SecretValue

__all__ = [
    "Authorizer",
    "AuthzError",
    "Permission",
    "PolicyDecision",
    "Principal",
    "SecretError",
    "SecretRef",
    "SecretValue",
    "SecurityContext",
    "SecurityContextManager",
    "SecurityDeclarationError",
    "SecurityError",
    "TenancyError",
    "__version__",
    "requires",
    "tenant_scoped",
]
