"""Ambient security context management across call boundaries."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar, Token
from typing import ClassVar

from monitoring_suite.security.context.constants import security_context as const
from monitoring_suite.security.context.security_context import security_context_objects as objs


class SecurityContextManager:
    """Set, read, bind, and clear the ambient security context."""

    _context: ClassVar[ContextVar[objs.SecurityContext | None]] = ContextVar(const.CONTEXT_VAR_NAME, default=None)

    def set(self, ctx: objs.SecurityContext) -> Token[objs.SecurityContext | None]:
        """Store the context and return the reset token."""
        return self._context.set(ctx)

    def get(self) -> objs.SecurityContext | None:
        """Return the current context, or None when unset."""
        return self._context.get()

    def bind(
        self, *, principal: objs.Principal | None = None, tenant_id: str | None = None
    ) -> AbstractContextManager[None]:
        """Temporarily bind a fresh context, restoring the prior one on exit."""
        return self._bound(objs.SecurityContext(principal=principal, tenant_id=tenant_id))

    def clear(self, token: Token[objs.SecurityContext | None]) -> None:
        """Reset the context to its state before the matching set call."""
        self._context.reset(token)

    @contextmanager
    def _bound(self, context: objs.SecurityContext) -> Generator[None, None, None]:
        """Set the context for the with-block and reset it afterward."""
        token = self.set(context)
        try:
            yield
        finally:
            self.clear(token)
