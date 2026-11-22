"""Tenancy constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Error messages raised at the tenancy boundary (source-side; tests match against these via const.ERR_*)."""

ERR_TENANCY_NO_TENANT_BOUND: Final = "no tenant bound in security context"
ERR_TENANCY_BOUNDARY_VIOLATION: Final = "tenant boundary violation"
