"""Rate-limit error messages. Imported as const."""

from __future__ import annotations

from typing import Final

"""Default messages of the rate-limit error classes."""

ERR_API_LIMITER_CONSTRAINT_VIOLATED: Final[str] = "Rate limit constraint violated."
ERR_API_LIMITER_RATE_EXCEEDED: Final[str] = "Rate limit exceeded."
ERR_API_LIMITER_DECLARATION_INVALID: Final[str] = "Invalid throttle declaration."


"""Error class contract values: domain, codes and HTTP statuses."""

DOMAIN_API_LIMITER: Final[str] = "api_limiter"
CODE_THROTTLE_ERROR: Final[str] = "throttle_error"
HTTP_STATUS_TOO_MANY_REQUESTS: Final[int] = 429
CODE_RATE_LIMIT_EXCEEDED: Final[str] = "rate_limit_exceeded"
CODE_THROTTLE_DECLARATION_INVALID: Final[str] = "throttle_declaration_invalid"
HTTP_STATUS_INTERNAL_SERVER_ERROR: Final[int] = 500
