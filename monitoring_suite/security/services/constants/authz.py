"""Authorization constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Denial reasons returned in PolicyDecision and raised via AuthzError (source-side; tests match against these via const.ERR_*)."""

ERR_AUTHZ_NO_PRINCIPAL: Final = "no authenticated principal"
ERR_AUTHZ_MISSING_SCOPE: Final = "missing scope {scope}"
