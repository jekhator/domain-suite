"""Error hierarchy for aspect composition."""

from __future__ import annotations

from monitoring_suite.aspects.errors.aspects_errors import (
    AspectDeclarationError,
    AspectsError,
)

__all__ = ["AspectsError", "AspectDeclarationError"]
