"""Aspect composition service for stacking cross-cutting decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar, Final, get_args

from domain_aspects.errors.aspects_errors import AspectDeclarationError
from domain_aspects.errors.constants import aspects as errors_const
from domain_aspects.services.aspects import aspects_objects as objs
from domain_aspects.services.constants import aspects as const


class Aspects:
    """Compose and apply aspect decorators in canonical order.

    Validates duplicate kinds and unknown entry types at decoration time.
    """

    _ENTRY_TYPES: ClassVar[tuple[type, ...]] = get_args(objs.AspectEntry)
    _ORDER_INDEX: ClassVar[dict[str, int]] = {
        kind: index for index, kind in enumerate(const.ASPECT_ORDER)
    }

    def __call__(
        self,
        *entries: objs.AspectEntry | frozenset[objs.AspectEntry],
    ) -> Callable:
        """Apply aspect decorators to the target function or class.

        Flattens frozensets, validates, sorts by ASPECT_ORDER, applies innermost-first.
        """
        flattened = self._flatten(entries)
        self._validate(flattened)
        sorted_entries = self._sort(flattened)

        def decorator(target: Callable) -> Callable:
            result = target
            for entry in reversed(sorted_entries):
                decorator_fn = entry.build()
                result = decorator_fn(result)
            return result

        return decorator

    def _flatten(
        self,
        entries: tuple[objs.AspectEntry | frozenset[objs.AspectEntry], ...],
    ) -> list[objs.AspectEntry]:
        """Flatten mixed single entries and frozensets into a flat list."""
        result: list[objs.AspectEntry] = []
        for entry in entries:
            if isinstance(entry, frozenset):
                result.extend(entry)
            else:
                result.append(entry)
        return result

    def _validate(self, entries: list[objs.AspectEntry]) -> None:
        """Validate no duplicates, no unknown types, not empty."""
        if not entries:
            raise AspectDeclarationError(
                message=errors_const.ERR_ASPECTS_EMPTY_DECLARATION
            )

        seen_kinds: set[str] = set()
        for entry in entries:
            if not isinstance(entry, self._ENTRY_TYPES):
                raise AspectDeclarationError(
                    message=errors_const.ERR_ASPECTS_UNKNOWN_ENTRY_TYPE.format(
                        entry_type=type(entry).__name__
                    )
                )
            kind = entry.kind
            if kind in seen_kinds:
                raise AspectDeclarationError(
                    message=errors_const.ERR_ASPECTS_DUPLICATE_KIND.format(kind=kind)
                )
            seen_kinds.add(kind)

    def _sort(self, entries: list[objs.AspectEntry]) -> list[objs.AspectEntry]:
        """Sort entries by ASPECT_ORDER; kinds outside the order sort last."""
        unordered_rank: Final = len(self._ORDER_INDEX)
        return sorted(
            entries,
            key=lambda entry: self._ORDER_INDEX.get(entry.kind, unordered_rank),
        )


aspects: Final = Aspects()
"""Module-level entrypoint for aspect composition."""
