"""Authorization: scope-based policy evaluation over permissions and decisions."""

from monitoring_suite.security.services.authz.authz_client import Authorizer
from monitoring_suite.security.services.authz.authz_objects import Permission, PolicyDecision

__all__ = ["Authorizer", "Permission", "PolicyDecision"]
