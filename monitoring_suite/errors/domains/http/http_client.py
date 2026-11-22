"""HTTP exception-family domain classifier."""

from __future__ import annotations

from monitoring_suite.errors.domains.constants import http as const


class HttpClassifier:
    """Classify httpx, requests, and aiohttp exceptions into the http domain."""

    def classify(self, err: BaseException) -> str | None:
        """Return const.HTTP when err originates in an HTTP-client library, else None."""
        if type(err).__module__.split(const.MODULE_SEPARATOR)[0] in const.HTTP_LIBRARIES:
            return const.HTTP
        return None


http = HttpClassifier()
