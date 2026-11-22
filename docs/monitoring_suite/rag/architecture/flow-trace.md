# monitoring_suite.rag: Flow-Trace

## Overview

Vendor-neutral wrapper around RAG retrieval calls that emits structured, HIPAA-auditable provenance events. Wraps callables and classes, capturing query input and chunk results, emitting `RetrievalProvenance` (query, chunk_ids, source_document_ids, principal_id, session_id, outcome, duration) to a configurable `ProvenanceSink`. Default sink is `NullProvenanceSink` (no-op); `ProvenanceRegistry` provides global default-sink binding. Preserves sync/async dispatch. Never swallows exceptions.

## Entry Unit

`@traced_retrieval(principal_id="usr_123", session_id="sess_456", sink=None)` decorator ──▶ `RetrievalProvenance` emission.

## Flow-Trace Diagram

```
① CONSTRUCT RetrievalProvenance [FROZEN,slots]
   query: str  ← retrieval query
   chunk_ids: tuple[str, ...]  ← retrieved chunk identifiers
   source_document_ids: tuple[str, ...]  ← source document identifiers
   principal_id: str  ← user/principal identifier for audit
   session_id: str  ← session identifier for audit trail
   outcome: ProvenanceOutcome  ← ProvenanceOutcome.SUCCESS | ProvenanceOutcome.FAILURE
   duration_ms: float  ← elapsed time in milliseconds
   occurred_at: str  ← ISO 8601 timestamp

   ProvenanceOutcome ← StrEnum: SUCCESS="success", FAILURE="failure"

② CONSTRUCT ProvenanceSink [PROTOCOL]
   ProvenanceSink.record(event: RetrievalProvenance) -> None  ← abstract method

   Implementations:
   ├─ NullProvenanceSink()  ← no-op, default
   ├─ CollectingProvenanceSink()  ← in-memory list for testing/dev
   └─ custom sinks (e.g., OpenTelemetry, LangSmith, Langfuse adapters)

③ DECORATE @traced_retrieval
   @traced_retrieval(principal_id="usr_123", session_id="sess_456", sink=None)  ──▶ traced_retrieval(principal_id, session_id, sink)
      ├─ decorator(target)
      │  ├─ isclass(target)?
      │  │  ├─ YES ──▶ _trace_class(target, principal_id, session_id, sink)
      │  │  │  ├─ _get_public_methods(cls)  ← skip _-prefixed, inherited, special
      │  │  │  ├─ for method_name in public_methods
      │  │  │  │  ├─ original_method = getattr(cls, method_name)
      │  │  │  │  ├─ traced_method = _trace_callable(original_method, principal_id, session_id, sink)
      │  │  │  │  └─ setattr(cls, method_name, traced_method)
      │  │  │  └─ returns cls
      │  │  └─ NO (callable) ──▶ _trace_callable(target, principal_id, session_id, sink)
      │  │     ├─ asyncio.iscoroutinefunction(fn)?
      │  │     │  ├─ YES ──▶ _wrap_async(fn, principal_id, session_id, sink)
      │  │     │  └─ NO  ──▶ _wrap_sync(fn, principal_id, session_id, sink)
      │  │     └─ returns wrapped callable
      └─ returns wrapped target

④ RUNTIME (sync path) ──▶ wrapper(*args, **kwargs)
      ├─ start_time = datetime.now(timezone.utc)
      ├─ actual_sink = sink or ProvenanceRegistry.get_default_sink()  ← resolve sink
      ├─ query_str = str(kwargs.get("query", args[0] if args else ""))  ← extract query
      ├─ try:
      │  ├─ result = fn(*args, **kwargs)  ← execute retrieval
      │  ├─ end_time = datetime.now(timezone.utc)
      │  ├─ duration_ms = (end_time - start_time).total_seconds() * 1000
      │  ├─ extract chunk_ids, source_document_ids from result
      │  ├─ provenance = RetrievalProvenance.for_success(query=query_str, chunk_ids=..., source_document_ids=..., principal_id=principal_id, session_id=session_id, duration_ms=duration_ms, occurred_at=end_time.isoformat())
      │  ├─ actual_sink.record(provenance)  ← send to sink
      │  └─ return result
      └─ except Exception:
         ├─ end_time = datetime.now(timezone.utc)
         ├─ duration_ms = (end_time - start_time).total_seconds() * 1000
         ├─ provenance = RetrievalProvenance.for_failure(query=query_str, principal_id=principal_id, session_id=session_id, duration_ms=duration_ms, occurred_at=end_time.isoformat())
         ├─ actual_sink.record(provenance)  ← send to sink
         └─ raise  ← exception propagates unchanged

⑤ RUNTIME (async path) ──▶ async async_wrapper(*args, **kwargs)
      ├─ start_time = datetime.now(timezone.utc)
      ├─ actual_sink = sink or ProvenanceRegistry.get_default_sink()
      ├─ query_str = str(kwargs.get("query", args[0] if args else ""))
      ├─ try:
      │  ├─ result = await fn(*args, **kwargs)  ← execute async retrieval
      │  ├─ end_time = datetime.now(timezone.utc)
      │  ├─ duration_ms = (end_time - start_time).total_seconds() * 1000
      │  ├─ extract chunk_ids, source_document_ids from result
      │  ├─ provenance = RetrievalProvenance.for_success(...)
      │  ├─ actual_sink.record(provenance)
      │  └─ return result
      └─ except Exception:
         ├─ [same as sync failure branch]
         └─ raise

⑥ REGISTRY BINDING
   ProvenanceRegistry.set_default_sink(sink)  ← global default for @traced_retrieval(..., sink=None)
   ProvenanceRegistry.get_default_sink()  ← returns _default_sink or NullProvenanceSink()
   ProvenanceRegistry.clear_default_sink()  ← reset

REAL OUTPUT (success):
   EMITTED RetrievalProvenance: retrieve
     query: "how accessible is this document?"
     chunk_ids: ("chunk_1", "chunk_2")
     source_document_ids: ("doc_123",)
     principal_id: "user_456"
     session_id: "sess_789"
     outcome: success
     duration_ms: 45.2
     occurred_at: 2026-07-13T14:32:15.123456+00:00

REAL OUTPUT (failure):
   EMITTED RetrievalProvenance: retrieve
     query: "query text"
     chunk_ids: ()
     source_document_ids: ()
     principal_id: "user_456"
     session_id: "sess_789"
     outcome: failure
     is_failure: True
     duration_ms: 12.5
```

## Key Constants

- `ProvenanceOutcome.SUCCESS` = "success"
- `ProvenanceOutcome.FAILURE` = "failure"
- `ERR_RETRIEVAL_INVALID_TARGET` = "retrieval target must be callable or class"
- `ERR_RETRIEVAL_EMPTY_CLASS` = "class has no public methods to trace"

## Core Classes

- `RetrievalProvenance` ← frozen slots; query, chunk_ids, source_document_ids, principal_id, session_id, outcome, duration_ms, occurred_at; __hash__; for_success(), for_failure() classmethods; is_failure property
- `ProvenanceOutcome` ← StrEnum; SUCCESS, FAILURE
- `ProvenanceSink` ← Protocol; record(event: RetrievalProvenance) -> None
- `NullProvenanceSink` ← no-op implementation
- `CollectingProvenanceSink` ← in-memory list; record(), events property, clear()
- `ProvenanceRegistry` ← static methods; set_default_sink(), get_default_sink(), clear_default_sink()

## Design Notes

- Provenance is recorded even on exception (never swallow; exception propagates after record)
- Default NullProvenanceSink ensures @traced_retrieval is safe without explicit sink binding
- Principal and session IDs are required for audit trail compliance
- Sink protocol is vendor-neutral; adapters (OpenTelemetry, LangSmith, etc.) implement ProvenanceSink
- Class decoration fans out to public methods
- Duration includes exception-handling time (start to end, always)
