# domain_rag: Flow-Trace

## Overview

A vendor-neutral wrapper around retrieval calls that emits a
`RetrievalProvenance` event per call to a `ProvenanceSink`: a success event
carrying the query, chunk ids and source document ids when the call returns,
or a failure event when it raises. The call's own result or exception is
returned or re-raised unchanged. Sync and async callables keep their dispatch.

## Entry Unit

`@traced_retrieval(principal_id, session_id, sink=None)` decorator, applied to
a callable or a class. `principal_id` and `session_id` must be non-empty.

## Flow-Trace Diagram

```
1. CONSTRUCT RetrievalProvenance [FROZEN, slots]
   query: str
   chunk_ids: tuple[str, ...]
   source_document_ids: tuple[str, ...]
   principal_id: str
   session_id: str
   outcome: ProvenanceOutcome     SUCCESS or FAILURE
   duration_ms: float             monotonic clock
   occurred_at: str               ISO 8601 timestamp of the end of the call

   Validation (ValueError): empty query, principal_id, session_id or
   occurred_at; negative duration_ms.

2. ProvenanceSink [PROTOCOL]
   record(event: RetrievalProvenance) -> None

   Implementations:
   - NullProvenanceSink()        no-op, used when no sink is bound
   - CollectingProvenanceSink()  in-memory list for tests and development

3. DECORATE @traced_retrieval
   traced_retrieval(principal_id, session_id, sink)
   - empty principal_id or session_id -> RetrievalDeclarationError
   - decorator(target)
     - class?      -> _trace_class: each public function or method defined on
                      the class itself is wrapped; classmethods and
                      staticmethods keep their descriptor type
     - callable?   -> _trace_callable: coroutine function -> async wrapper,
                      otherwise sync wrapper
     - anything else -> RetrievalDeclarationError

4. RUNTIME (sync) wrapper(*args, **kwargs)
   - started = perf_counter()
   - actual_sink = sink, or ProvenanceRegistry.get_default_sink() when sink is None
   - query = kwargs["query"], else the second positional argument, else the
     first positional argument, else the placeholder "(no query)"; an empty
     value also becomes the placeholder
   - try:
       result = fn(*args, **kwargs)
     except Exception as error:
       _record_failure(...)  a sink error is attached to `error` as a note
       raise
   - _record_success(...)    chunk_ids and source_document_ids come from a list or
                             tuple result, or from the matching keys of a dict
                             result; any other value yields an empty tuple. A sink
                             error propagates to the caller.
   - return result

5. RUNTIME (async) async_wrapper(*args, **kwargs)
   - same sequence, with `await fn(*args, **kwargs)` in the try block

6. REGISTRY BINDING
   ProvenanceRegistry.set_default_sink(sink)  global default for sink=None
   ProvenanceRegistry.get_default_sink()      returns the bound sink (identity check),
                                              or the shared NullProvenanceSink
   ProvenanceRegistry.clear_default_sink()    resets to unset

REAL OUTPUT (success and failure):
   EMITTED RetrievalProvenance: 'how accessible is this document?'
     chunk_ids: ('chunk_1', 'chunk_2')
     source_document_ids: ('doc_123',)
     principal_id: user_456
     session_id: sess_789
     outcome: success
     is_failure: False
   EMITTED RetrievalProvenance: 'query text'
     chunk_ids: ()
     source_document_ids: ()
     principal_id: user_456
     session_id: sess_789
     outcome: failure
     is_failure: True
```

## Key Constants

- `ProvenanceOutcome.SUCCESS` = "success"
- `ProvenanceOutcome.FAILURE` = "failure"
- `NO_QUERY_PLACEHOLDER` = "(no query)"
- `ERR_RETRIEVAL_INVALID_TARGET` = "Invalid retrieval target: must be a callable or class"
- `ERR_RETRIEVAL_EMPTY_CLASS` = "Cannot trace class with no public methods"
- `ERR_RETRIEVAL_EMPTY_PRINCIPAL` = "Retrieval principal_id must be non-empty"
- `ERR_RETRIEVAL_EMPTY_SESSION` = "Retrieval session_id must be non-empty"

## Core Classes

- `RetrievalProvenance`: frozen slots dataclass; `for_success()` and `for_failure()` classmethods; `is_failure` property
- `ProvenanceOutcome`: StrEnum with `SUCCESS` and `FAILURE`
- `ProvenanceSink`: Protocol with `record(event)`
- `NullProvenanceSink`: no-op implementation
- `CollectingProvenanceSink`: in-memory list with `record()`, an `events` copy property and `clear()`
- `ProvenanceRegistry`: class methods `set_default_sink()`, `get_default_sink()`, `clear_default_sink()`

## Design Notes

- Failures are recorded and the original exception propagates unchanged; a recording failure is attached to it as a note.
- A successful call whose provenance cannot be recorded raises the sink error, so a missing audit record is visible.
- The wrapped call's result is never changed by tracing.
- Principal and session ids are required at declaration time for the audit trail.
- The sink protocol is vendor-neutral; adapters (OpenTelemetry, LangSmith, etc.) implement `ProvenanceSink`.
- Class decoration covers functions and method descriptors defined on the class itself. Inherited methods are not wrapped; an override is.
