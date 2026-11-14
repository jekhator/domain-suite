# domain-rag

Vendor-neutral wrapper for RAG retrieval provenance tracking with audit-ready records.

## Overview

`domain-rag` provides:

- **Retrieval provenance tracking**: Capture the query, chunk ids and source document ids for each retrieval
- **Audit fields**: Each event carries principal_id, session_id, timestamps and outcome
- **Pluggable sinks**: Emit provenance to any system that implements `record(event)`
- **Decorator-based**: Apply tracing with the `@traced_retrieval` decorator
- **Result-preserving**: Tracing never changes what the wrapped call returns or raises

## Quick Start

```python
from domain_rag import CollectingProvenanceSink, ProvenanceRegistry, traced_retrieval

sink = CollectingProvenanceSink()
ProvenanceRegistry.set_default_sink(sink)


@traced_retrieval("usr_123", "sess_456")
def retrieve(query: str):
    return {"chunk_ids": ["chunk_1", "chunk_2"], "source_document_ids": ["doc_abc"]}


result = retrieve("what is RAG?")
event = sink.events[0]
print(result)
print(event.query, event.chunk_ids, event.source_document_ids, event.outcome)
```

**Output (Python 3.12, domain-suite==0.7.0):**
```
{'chunk_ids': ['chunk_1', 'chunk_2'], 'source_document_ids': ['doc_abc']}
what is RAG? ('chunk_1', 'chunk_2') ('doc_abc',) success
```

## Public API

- **`traced_retrieval`**: Decorator that records a provenance event for each call
- **`ProvenanceRegistry`**: Global registry for the default sink
- **`RetrievalProvenance`**: Immutable event with query, chunk ids, source ids, principal, session, outcome and timing
- **`ProvenanceSink`**: Protocol for sinks (`record(event) -> None`)
- **`CollectingProvenanceSink`**: In-memory collector for tests and development
- **`NullProvenanceSink`**: No-op sink (default)
- **`ProvenanceOutcome`**: `SUCCESS` or `FAILURE`
- Retrieval error classes: `RetrievalError`, `RetrievalDeclarationError`

## Features

### Per-Feature Documentation

- **[architecture/flow-trace.md](architecture/flow-trace.md)**: Flow and runtime behaviour
- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Basic Retrieval Tracing

```python
from domain_rag import (
    traced_retrieval,
    CollectingProvenanceSink,
    ProvenanceRegistry,
)

# Set up sink
sink = CollectingProvenanceSink()
ProvenanceRegistry.set_default_sink(sink)

# Trace a retrieval function
@traced_retrieval(principal_id="user_789", session_id="sess_abc")
def retrieve_chunks(query: str):
    return {
        "chunk_ids": ["chunk_a", "chunk_b"],
        "source_document_ids": ["source_1"],
    }

# Call the function
result = retrieve_chunks("what is accessibility?")

# Inspect provenance events
for event in sink.events:
    print(f"Query: {event.query}")
    print(f"Chunks: {event.chunk_ids}")
    print(f"Principal: {event.principal_id}")
    print(f"Outcome: {event.outcome}")
```

**Output (Python 3.12, domain-suite==0.7.0):**
```
Query: what is accessibility?
Chunks: ('chunk_a', 'chunk_b')
Principal: user_789
Outcome: success
```

### Custom Sink Implementation

Implement the `ProvenanceSink` protocol to forward events to your own system:

```python
from domain_rag import ProvenanceSink, RetrievalProvenance, traced_retrieval


class ListSink:
    """Keep the outcome and query of each event."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str]] = []

    def record(self, event: RetrievalProvenance) -> None:
        self.rows.append((event.query, event.outcome.value))


sink: ProvenanceSink = ListSink()


@traced_retrieval(principal_id="user_123", session_id="sess_456", sink=sink)
def retrieve(query: str):
    return {"chunk_ids": ["c1"], "source_document_ids": ["d1"]}


retrieve("policy")
print(sink.rows)
```

### Class Decoration

Apply tracing to all public methods defined on the class:

```python
from dataclasses import dataclass

from domain_rag import CollectingProvenanceSink, traced_retrieval


@traced_retrieval(principal_id="user_123", session_id="sess_456")
@dataclass(frozen=True, slots=True)
class RAGService:
    index_name: str

    def search(self, query: str):
        return {
            "chunk_ids": ["chunk_1"],
            "source_document_ids": ["doc_1"],
        }

    def rerank(self, docs):
        return sorted(docs)


service = RAGService(index_name="my_index")
results = service.search("query")
```

### Async Retrieval

Tracing works with async functions:

```python
import asyncio

from domain_rag import traced_retrieval


@traced_retrieval(principal_id="user_123", session_id="sess_456")
async def async_retrieve(query: str):
    await asyncio.sleep(0.1)
    return {
        "chunk_ids": ["chunk_1"],
        "source_document_ids": ["doc_1"],
    }


result = asyncio.run(async_retrieve("query"))
```

### Failures and Sink Errors

A failing call is recorded with its query text, and the original exception is
raised unchanged. If the sink also fails on that path, its error is
added to the exception as a note. A successful call whose sink fails raises the
sink error, so a missing audit record is never silent.

## Integration with domain-aspects

Compose with other aspects:

```python
from domain_aspects import Logged, aspects
from domain_rag import traced_retrieval


@aspects(
    Logged(event="rag.retrieve"),
)
@traced_retrieval(principal_id="user_123", session_id="sess_456")
def retrieve(query: str):
    return {"chunk_ids": ["c1"], "source_document_ids": ["d1"]}
```

## Next Steps

- Read the [main domain-suite README](../../README.md) for installation and examples
- Explore [architecture/flow-trace.md](architecture/flow-trace.md) for the runtime sequence
- Implement a sink for your audit or observability system
