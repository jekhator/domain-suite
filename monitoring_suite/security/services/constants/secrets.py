"""Secrets constants. Imported as const."""

from __future__ import annotations

from typing import Final

"""Masked repr token for resolved secrets."""

SECRET_VALUE_MASKED_REPR: Final[str] = "<SecretValue ***>"


"""Error messages raised during secret resolution (source-side; tests match against these via const.ERR_*)."""

ERR_SECRETS_NO_BACKEND: Final[str] = "no secrets backend provided"
