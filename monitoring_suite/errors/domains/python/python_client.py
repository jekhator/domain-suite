"""Stdlib exception-family domain classifier."""

from __future__ import annotations

from monitoring_suite.errors.domains.constants import python as const


class PythonClassifier:
    """Classify stdlib exceptions into coarse domains."""

    _FAMILIES: tuple[tuple[tuple[type[BaseException], ...], str], ...] = (
        ((ConnectionError, TimeoutError), const.NETWORK),
        ((FileNotFoundError, PermissionError, OSError), const.OS),
        ((ValueError, KeyError, TypeError), const.LOGIC),
        ((AssertionError,), const.ASSERTION),
    )

    def classify(self, err: BaseException) -> str | None:
        """Return err's stdlib domain, or None when no family matches."""
        for types, domain in self._FAMILIES:
            if isinstance(err, types):
                return domain
        return None


python = PythonClassifier()
