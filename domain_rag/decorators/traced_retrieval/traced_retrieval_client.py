"""Traced retrieval decorator for automatic provenance emission."""

import asyncio
import functools
import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional, cast

from domain_rag.errors.constants import retrieval as const
from domain_rag.errors.retrieval_errors import RetrievalDeclarationError
from domain_rag.services.provenance.provenance_client import ProvenanceSink
from domain_rag.services.provenance.provenance_objects import RetrievalProvenance
from domain_rag.services.registry.registry_client import ProvenanceRegistry


class TracedRetrievalClient:
    """Container for traced retrieval decorator and helper methods."""

    @staticmethod
    def traced_retrieval[Target](
        principal_id: str,
        session_id: str,
        sink: Optional[ProvenanceSink] = None,
    ) -> Callable[[Target], Target]:
        """Apply retrieval provenance tracking to callables and classes."""

        def decorator(target: Target) -> Target:
            """Apply tracing to target."""
            if inspect.isclass(target):
                return cast(
                    Target,
                    TracedRetrievalClient._trace_class(
                        target, principal_id, session_id, sink
                    ),
                )
            elif callable(target):
                return cast(
                    Target,
                    TracedRetrievalClient._trace_callable(
                        target, principal_id, session_id, sink
                    ),
                )
            else:
                raise RetrievalDeclarationError(const.ERR_RETRIEVAL_INVALID_TARGET)

        return decorator

    @staticmethod
    def _trace_callable(
        fn: Callable[..., Any],
        principal_id: str,
        session_id: str,
        sink: Optional[ProvenanceSink],
    ) -> Callable[..., Any]:
        """Wrap a callable with retrieval provenance tracking."""
        if asyncio.iscoroutinefunction(fn):
            return TracedRetrievalClient._wrap_async(fn, principal_id, session_id, sink)
        else:
            return TracedRetrievalClient._wrap_sync(fn, principal_id, session_id, sink)

    @staticmethod
    def _wrap_sync(
        fn: Callable[..., Any],
        principal_id: str,
        session_id: str,
        sink: Optional[ProvenanceSink],
    ) -> Callable[..., Any]:
        """Wrap synchronous callable."""

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute with retrieval provenance tracking."""
            start_time = datetime.now(timezone.utc)
            actual_sink = sink or ProvenanceRegistry.get_default_sink()

            if "query" in kwargs:
                query_str = str(kwargs["query"])
            elif len(args) > 1:
                query_str = str(args[1])
            elif len(args) > 0:
                query_str = str(args[0])
            else:  # pragma: no cover
                query_str = ""

            try:
                result = fn(*args, **kwargs)
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000

                chunk_ids = ()
                source_document_ids = ()
                if isinstance(result, dict):
                    chunk_ids = tuple(result.get("chunk_ids", []))
                    source_document_ids = tuple(result.get("source_document_ids", []))
                elif isinstance(result, (list, tuple)):
                    chunk_ids = tuple(result)

                provenance = RetrievalProvenance.for_success(
                    query=query_str,
                    chunk_ids=chunk_ids,
                    source_document_ids=source_document_ids,
                    principal_id=principal_id,
                    session_id=session_id,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                )
                actual_sink.record(provenance)
                return result
            except Exception:
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000
                provenance = RetrievalProvenance.for_failure(
                    query=query_str,
                    principal_id=principal_id,
                    session_id=session_id,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                )
                actual_sink.record(provenance)
                raise

        return wrapper

    @staticmethod
    def _wrap_async(
        fn: Callable[..., Any],
        principal_id: str,
        session_id: str,
        sink: Optional[ProvenanceSink],
    ) -> Callable[..., Any]:
        """Wrap asynchronous callable."""

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute async with retrieval provenance tracking."""
            start_time = datetime.now(timezone.utc)
            actual_sink = sink or ProvenanceRegistry.get_default_sink()

            if "query" in kwargs:
                query_str = str(kwargs["query"])
            elif len(args) > 1:
                query_str = str(args[1])
            elif len(args) > 0:
                query_str = str(args[0])
            else:  # pragma: no cover
                query_str = ""

            try:
                result = await fn(*args, **kwargs)
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000

                chunk_ids = ()
                source_document_ids = ()
                if isinstance(result, dict):
                    chunk_ids = tuple(result.get("chunk_ids", []))
                    source_document_ids = tuple(result.get("source_document_ids", []))
                elif isinstance(result, (list, tuple)):
                    chunk_ids = tuple(result)

                provenance = RetrievalProvenance.for_success(
                    query=query_str,
                    chunk_ids=chunk_ids,
                    source_document_ids=source_document_ids,
                    principal_id=principal_id,
                    session_id=session_id,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                )
                actual_sink.record(provenance)
                return result
            except Exception:
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000
                provenance = RetrievalProvenance.for_failure(
                    query=query_str,
                    principal_id=principal_id,
                    session_id=session_id,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                )
                actual_sink.record(provenance)
                raise

        return async_wrapper

    @staticmethod
    def _trace_class(
        cls: type,
        principal_id: str,
        session_id: str,
        sink: Optional[ProvenanceSink],
    ) -> type:
        """Fan out tracing to public methods on a class."""
        public_methods = TracedRetrievalClient._get_public_methods(cls)

        if not public_methods:
            raise RetrievalDeclarationError(const.ERR_RETRIEVAL_EMPTY_CLASS)

        for method_name in public_methods:
            original_method = getattr(cls, method_name)
            traced_method = TracedRetrievalClient._trace_callable(
                original_method, principal_id, session_id, sink
            )
            setattr(cls, method_name, traced_method)

        return cls

    @staticmethod
    def _get_public_methods(cls: type) -> list[str]:
        """Get public method names from class, excluding inherited and special methods."""
        public = []

        for name, value in inspect.getmembers(cls):
            if name.startswith("_"):
                continue
            if inspect.ismethod(value) or inspect.isfunction(value):
                if not hasattr(cls, "__bases__") or name not in dir(cls.__bases__[0]):
                    public.append(name)
            elif isinstance(value, classmethod):  # pragma: no cover
                public.append(name)
            elif isinstance(value, staticmethod):  # pragma: no cover
                public.append(name)

        return public


traced_retrieval = TracedRetrievalClient.traced_retrieval
