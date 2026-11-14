"""Declaration introspection: read and collect attached throttle policies."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

from domain_api_limiter.services.constants import policy as const
from domain_api_limiter.services.policy import policy_objects as objs


class PolicyRegistry:
    """Read and collect throttle declarations attached by the throttled decorator."""

    def policy_of(self, target: Callable[..., object]) -> objs.ThrottlePolicy | None:
        """Return the policy declared on the target, or None."""
        policy = getattr(target, const.THROTTLE_POLICY_ATTR, None)
        return policy if isinstance(policy, objs.ThrottlePolicy) else None

    def collect(self, container: type | ModuleType) -> tuple[objs.ThrottlePolicy, ...]:
        """Collect all declared policies from class or module members.

        Preserves definition order. Handles instance methods, classmethod,
        and staticmethod decorators.
        """
        policies: list[objs.ThrottlePolicy] = []
        for member in vars(container).values():
            if isinstance(member, (classmethod, staticmethod)):
                policy = self.policy_of(member.__func__)
                if policy is not None:
                    policies.append(policy)
            elif callable(member):
                policy = self.policy_of(member)
                if policy is not None:
                    policies.append(policy)
        return tuple(policies)
