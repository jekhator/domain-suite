"""Tenant-scoped decorator constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Sentinel selecting the instance attribute as the tenant source."""

SELF_TENANT_ID: Final[str] = "self.tenant_id"


"""Error messages raised during tenant argument extraction (source-side; tests match against these via const.ERR_*)."""

ERR_TENANT_SCOPED_UNBOUND_SELF: Final[str] = "self.tenant_id requires a bound method call"
ERR_TENANT_SCOPED_PARAM_MISSING: Final[str] = "tenant parameter missing from call"


"""Decorator declaration validation messages."""

ERR_TENANT_SCOPED_MISSING_PARAM: Final[str] = (
    "Method lacks required tenant parameter at class-level decoration."
)
