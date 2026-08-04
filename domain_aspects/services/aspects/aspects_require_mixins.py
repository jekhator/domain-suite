"""Mixin composition validation aspect."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain_aspects.services.constants import aspects as const

if TYPE_CHECKING:
    from domain_aspects.services.aspects.aspects_objects import AspectKind


@dataclass(frozen=True, slots=True)
class RequireMixins:
    """Composition validation marker: class must inherit all specified mixin bases.

    Validate-only marker (no runtime wrapper). Performed at composition time, fails loudly.
    Class-target only; function targets rejected.
    """

    bases: tuple[type, ...] = ()

    def __post_init__(self) -> None:
        if not self.bases or not isinstance(self.bases, tuple):
            raise ValueError(const.ERR_ASPECT_REQUIRE_MIXINS_BASES_INVALID)

    @property
    def kind(self) -> str:
        from domain_aspects.services.aspects.aspects_objects import AspectKind

        return AspectKind.REQUIRE_MIXINS

    def build(self) -> Callable:
        """Build validation marker for class-target only."""
        required_bases = self.bases

        def decorator(target: Callable) -> Callable:
            if not inspect.isclass(target):
                raise ValueError(const.ERR_ASPECT_REQUIRE_MIXINS_FUNCTION_TARGET)

            missing = [base for base in required_bases if not issubclass(target, base)]
            if missing:
                missing_names = ", ".join(base.__name__ for base in missing)
                raise ValueError(
                    const.ERR_ASPECT_REQUIRE_MIXINS_MISSING_BASES.format(
                        class_name=target.__name__, missing_bases=missing_names
                    )
                )

            return target

        return decorator
