"""Class-level fan-out shared by the aspect builders that decorate class methods."""

from __future__ import annotations

from collections.abc import Callable


class ClassFanout:
    """Apply a per-method wrapper to the public methods declared on a class."""

    @staticmethod
    def decorate_class(
        target_class: type,
        marker: str,
        decorate: Callable[[Callable[..., object]], Callable[..., object]],
    ) -> type:
        """Rewrap each eligible method in the class dict, preserving class and static method kinds."""
        for name, method in list(target_class.__dict__.items()):
            if name.startswith("_"):
                continue
            if isinstance(method, (property, type)):
                continue

            is_classmethod = isinstance(method, classmethod)
            is_staticmethod = isinstance(method, staticmethod)
            unwrapped = method.__func__ if is_classmethod or is_staticmethod else method

            if not callable(unwrapped):
                continue
            if hasattr(unwrapped, marker):
                continue

            decorated = decorate(unwrapped)
            if is_classmethod:
                setattr(target_class, name, classmethod(decorated))
            elif is_staticmethod:
                setattr(target_class, name, staticmethod(decorated))
            else:
                setattr(target_class, name, decorated)
        return target_class
