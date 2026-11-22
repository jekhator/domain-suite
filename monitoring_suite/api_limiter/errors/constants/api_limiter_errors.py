"""Rate-limit error messages. Imported as const."""

from __future__ import annotations

from typing import Final

"""Default messages of the rate-limit error classes."""

ERR_API_LIMITER_CONSTRAINT_VIOLATED: Final[str] = "Rate limit constraint violated."
ERR_API_LIMITER_RATE_EXCEEDED: Final[str] = "Rate limit exceeded."
ERR_API_LIMITER_DECLARATION_INVALID: Final[str] = "Invalid throttle declaration."
