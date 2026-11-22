"""Error messages raised at the API surface (source-side; tests match against these via const.ERR_*).

Imported as const.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ERR_AUTHZ_PERMISSION_DENIED",
    "ERR_SECRET_ACCESS_FAILED",
    "ERR_SECURITY_CONSTRAINT_VIOLATED",
    "ERR_TENANCY_BOUNDARY_VIOLATION",
    "ERR_SECURITY_DECLARATION_FAILED",
]


"""Security constraint messages."""

ERR_SECURITY_CONSTRAINT_VIOLATED: Final = "Security constraint violated."

ERR_AUTHZ_PERMISSION_DENIED: Final = "Permission denied."

ERR_TENANCY_BOUNDARY_VIOLATION: Final = "Tenant boundary violation."

ERR_SECRET_ACCESS_FAILED: Final = "Secret access failed."


"""Decorator declaration-time validation messages."""

ERR_SECURITY_DECLARATION_FAILED: Final = "Security decorator declaration failed."
