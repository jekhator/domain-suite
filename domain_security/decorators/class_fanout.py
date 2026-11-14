"""Class-level fan-out shared by the declarative security decorators."""

from __future__ import annotations

import inspect
from collections.abc import Callable


class ClassFanout:
    """Apply a per-method decorator to the public methods declared on a class."""

    @staticmethod
    def should_decorate(name: str, obj: object, marker: str) -> bool:
        """Check if a class attribute should be decorated."""
        if name.startswith("_") or inspect.isbuiltin(obj):
            return False
        if isinstance(obj, property):
            return False
        if inspect.isclass(obj):
            return False
        if hasattr(obj, marker):
            return False
        return callable(obj) or isinstance(obj, (classmethod, staticmethod))

    @staticmethod
    def decorate_class(
        cls: type,
        marker: str,
        decorate: Callable[[str, Callable[..., object]], Callable[..., object]],
    ) -> type:
        """Rewrite each eligible method in the class dict through the decorate callback."""
        for name, method in list(cls.__dict__.items()):
            if not ClassFanout.should_decorate(name, method, marker):
                continue
            if isinstance(method, classmethod):
                setattr(cls, name, classmethod(decorate(name, method.__func__)))
            elif isinstance(method, staticmethod):
                setattr(cls, name, staticmethod(decorate(name, method.__func__)))
            else:
                setattr(cls, name, decorate(name, method))
        return cls
