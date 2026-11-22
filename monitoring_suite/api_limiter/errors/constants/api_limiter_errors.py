"""Rate-limit error messages. Imported as const."""

from __future__ import annotations

from typing import Final

ERR_API_LIMITER_CONSTRAINT_VIOLATED: Final = "Rate limit constraint violated."
ERR_API_LIMITER_RATE_EXCEEDED: Final = "Rate limit exceeded."
ERR_API_LIMITER_DECLARATION_INVALID: Final = "Invalid throttle declaration."
