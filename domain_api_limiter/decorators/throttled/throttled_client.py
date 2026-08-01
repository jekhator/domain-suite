"""Declarative rate-limit policy attachment for service callables and classes."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from inspect import isclass
from typing import Any, TypeVar

from domain_api_limiter.errors.api_limiter_errors import ThrottleDeclarationError
from domain_api_limiter.services.constants import policy as const
from domain_api_limiter.services.policy.policy_objects import (
    RateLimit,
    ThrottlePolicy,
    TierRate,
)

Decorated = TypeVar("Decorated", bound=Callable[..., Any])


class Throttled:
    """Decorator factory attaching validated ThrottlePolicy to callables and classes."""

    def __call__(
        self,
        scope: str,
        rate: str,
        tiers: Mapping[str, str] | None = None,
    ) -> Callable[[Decorated | type], Decorated | type]:
        """Attach throttle policy to a callable or class.

        Applied to a callable: attaches policy with the given scope.
        Applied to a class: fans out to all public methods, scoped as
        '{root}:{method_name}'.
        """
        policy = ThrottlePolicy(
            scope=scope,
            rate=RateLimit.from_rate(rate),
            tier_rates=self._tier_rates(tiers),
        )

        def declare(target: Decorated | type) -> Decorated | type:
            if isclass(target):
                return self._decorate_class(target, policy)
            else:
                setattr(target, const.THROTTLE_POLICY_ATTR, policy)
                return target

        return declare

    def _decorate_class(self, cls: type, root_policy: ThrottlePolicy) -> type:
        """Fan out policy to all public methods in the class.

        Skips _-prefixed, dunders, properties, nested classes, and methods
        already decorated. Each method gets scope '{root}:{method_name}'.
        """
        public_methods = self._select_public_methods(cls)

        if not public_methods:
            raise ThrottleDeclarationError(
                message=const.ERR_POLICY_NO_PUBLIC_METHODS,
                class_name=cls.__name__,
            )

        for method_name, method_obj in public_methods:
            if hasattr(method_obj, const.THROTTLE_POLICY_ATTR):
                continue

            method_scope = f"{root_policy.scope}:{method_name}"
            method_policy = ThrottlePolicy(
                scope=method_scope,
                rate=root_policy.rate,
                tier_rates=root_policy.tier_rates,
            )
            setattr(method_obj, const.THROTTLE_POLICY_ATTR, method_policy)

        return cls

    def _select_public_methods(self, cls: type) -> list[tuple[str, Any]]:
        """Select callable members eligible for policy fanning.

        Returns (name, callable) pairs from cls.__dict__, skipping:
        _-prefixed names, dunders, nested classes, properties, and descriptors.
        """
        methods = []
        for name, member in cls.__dict__.items():
            if name.startswith("_"):
                continue

            if isclass(member):
                continue

            if isinstance(member, property):
                continue

            if isinstance(member, (classmethod, staticmethod)):
                methods.append((name, member.__func__))
                continue

            if callable(member):
                methods.append((name, member))

        return methods

    @staticmethod
    def _tier_rates(tiers: Mapping[str, str] | None) -> tuple[TierRate, ...]:
        """Build tier overrides from a tier-to-rate mapping."""
        if not tiers:
            return ()
        return tuple(
            TierRate(tier=tier, rate=RateLimit.from_rate(rate))
            for tier, rate in tiers.items()
        )


throttled = Throttled()
