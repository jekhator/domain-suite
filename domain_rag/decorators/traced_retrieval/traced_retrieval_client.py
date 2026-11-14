"""Traced retrieval decorator for automatic provenance emission."""

import asyncio
import functools
import inspect
import time
from collections.abc import Callable
from datetime import datetime, timezone
from types import FunctionType
from typing import Any, Optional, cast

from domain_rag.errors.constants import retrieval as const
from domain_rag.errors.retrieval_errors import RetrievalDeclarationError
from domain_rag.services.constants import provenance as provenance_const
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
        if not principal_id:
            raise RetrievalDeclarationError(const.ERR_RETRIEVAL_EMPTY_PRINCIPAL)
        if not session_id:
            raise RetrievalDeclarationError(const.ERR_RETRIEVAL_EMPTY_SESSION)

        def decorator(target: Target) -> Target:
            """Apply tracing to target."""
            if inspect.isclass(target):
                return cast(
                    Target,
                    TracedRetrievalClient._trace_class(
                        target, principal_id, session_id, sink
                    ),
                )
            if callable(target):
                return cast(
                    Target,
                    TracedRetrievalClient._trace_callable(
                        target, principal_id, session_id, sink
                    ),
                )
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
            started = time.perf_counter()
            actual_sink = TracedRetrievalClient._resolve_sink(sink)
            query = TracedRetrievalClient._query_from_call(args, kwargs)
            try:
                result = fn(*args, **kwargs)
            except Exception as error:
                TracedRetrievalClient._record_failure(
                    actual_sink, query, principal_id, session_id, started, error
                )
                raise
            TracedRetrievalClient._record_success(
                actual_sink, query, principal_id, session_id, started, result
            )
            return result

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
            started = time.perf_counter()
            actual_sink = TracedRetrievalClient._resolve_sink(sink)
            query = TracedRetrievalClient._query_from_call(args, kwargs)
            try:
                result = await fn(*args, **kwargs)
            except Exception as error:
                TracedRetrievalClient._record_failure(
                    actual_sink, query, principal_id, session_id, started, error
                )
                raise
            TracedRetrievalClient._record_success(
                actual_sink, query, principal_id, session_id, started, result
            )
            return result

        return async_wrapper

    @staticmethod
    def _resolve_sink(sink: Optional[ProvenanceSink]) -> ProvenanceSink:
        """Return the bound sink, falling back to the registry default when unset."""
        if sink is None:
            return ProvenanceRegistry.get_default_sink()
        return sink

    @staticmethod
    def _query_from_call(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """Return the query text from keyword, second positional, or first positional argument."""
        if provenance_const.QUERY_ARGUMENT in kwargs:
            candidate: Any = kwargs[provenance_const.QUERY_ARGUMENT]
        elif len(args) > 1:
            candidate = args[1]
        elif args:
            candidate = args[0]
        else:
            return provenance_const.NO_QUERY_PLACEHOLDER
        return str(candidate) or provenance_const.NO_QUERY_PLACEHOLDER

    @staticmethod
    def _ids_from(result: object, key: str) -> tuple[str, ...]:
        """Return id values from a result mapping, or from a sequence result itself."""
        if isinstance(result, dict):
            values = result.get(key, [])
            return tuple(values) if isinstance(values, (list, tuple)) else ()
        return ()

    @staticmethod
    def _chunk_ids_from(result: object) -> tuple[str, ...]:
        """Return chunk ids from a mapping result or a sequence result."""
        if isinstance(result, (list, tuple)):
            return tuple(result)
        return TracedRetrievalClient._ids_from(
            result, provenance_const.RESULT_CHUNK_IDS_KEY
        )

    @staticmethod
    def _record_success(
        sink: ProvenanceSink,
        query: str,
        principal_id: str,
        session_id: str,
        started: float,
        result: object,
    ) -> None:
        """Record a successful retrieval; a sink failure surfaces to the caller."""
        ended = datetime.now(timezone.utc)
        sink.record(
            RetrievalProvenance.for_success(
                query=query,
                chunk_ids=TracedRetrievalClient._chunk_ids_from(result),
                source_document_ids=TracedRetrievalClient._ids_from(
                    result, provenance_const.RESULT_SOURCE_IDS_KEY
                ),
                principal_id=principal_id,
                session_id=session_id,
                duration_ms=TracedRetrievalClient._elapsed_ms(started),
                occurred_at=ended.isoformat(),
            )
        )

    @staticmethod
    def _record_failure(
        sink: ProvenanceSink,
        query: str,
        principal_id: str,
        session_id: str,
        started: float,
        error: BaseException,
    ) -> None:
        """Record a failed retrieval without replacing the call's exception."""
        try:
            sink.record(
                RetrievalProvenance.for_failure(
                    query=query,
                    principal_id=principal_id,
                    session_id=session_id,
                    duration_ms=TracedRetrievalClient._elapsed_ms(started),
                    occurred_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        except Exception as recording_error:
            error.add_note(
                f"{provenance_const.NOTE_RECORDING_FAILED}: {recording_error!r}"
            )

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        """Return milliseconds elapsed since a perf_counter reading."""
        return (time.perf_counter() - started) * 1000

    @staticmethod
    def _trace_class(
        cls: type,
        principal_id: str,
        session_id: str,
        sink: Optional[ProvenanceSink],
    ) -> type:
        """Fan out tracing to public methods defined on a class."""
        public_methods = TracedRetrievalClient._get_public_methods(cls)

        if not public_methods:
            raise RetrievalDeclarationError(const.ERR_RETRIEVAL_EMPTY_CLASS)

        for method_name in public_methods:
            raw_method = vars(cls)[method_name]
            if isinstance(raw_method, classmethod):
                wrapped: Any = classmethod(
                    TracedRetrievalClient._trace_callable(
                        raw_method.__func__, principal_id, session_id, sink
                    )
                )
            elif isinstance(raw_method, staticmethod):
                wrapped = staticmethod(
                    TracedRetrievalClient._trace_callable(
                        raw_method.__func__, principal_id, session_id, sink
                    )
                )
            else:
                wrapped = TracedRetrievalClient._trace_callable(
                    raw_method, principal_id, session_id, sink
                )
            setattr(cls, method_name, wrapped)

        return cls

    @staticmethod
    def _get_public_methods(cls: type) -> list[str]:
        """List public functions and method descriptors defined on the class itself."""
        public: list[str] = []
        for name, value in vars(cls).items():
            if name.startswith("_"):
                continue
            if isinstance(value, (FunctionType, classmethod, staticmethod)):
                public.append(name)
        return public


traced_retrieval = TracedRetrievalClient.traced_retrieval
