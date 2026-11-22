# monitoring_suite.rag

Vendor-neutral wrapper for RAG retrieval provenance tracking with HIPAA-auditable audit trails.

## Overview

`monitoring_suite.rag` provides:

- **Retrieval provenance tracking**: Capture query, chunks, and sources for every retrieval
- **HIPAA-auditable events**: Record principal_id, session_id, timestamps, and outcomes
- **Pluggable sinks**: Emit provenance to external systems (OpenTelemetry, LangSmith, Langfuse, etc.)
- **Decorator-based**: Apply tracing with `@traced_retrieval` decorator
- **Never-swallow exceptions**: Exceptions propagate; provenance records before re-raising

## Quick Start

```python
from monitoring_suite.rag import traced_retrieval, CollectingProvenanceSink, ProvenanceRegistry

# Create a sink and set as default
sink = CollectingProvenanceSink()
ProvenanceRegistry.set_default_sink(sink)

# Apply tracing to a retrieval function
@traced_retrieval(principal_id="user_123", session_id="sess_456")
def retrieve_documents(query: str):
    results = {
        "chunk_ids": ["chunk_1", "chunk_2"],
        "source_document_ids": ["doc_abc"],
    }
    return results

# The decorator automatically tracks:
# - Query input
# - Retrieved chunk IDs and source document IDs
# - Success/failure outcomes
# - Latency (milliseconds)
# - Principal and session for audit trail
```

## Public API

- **`traced_retrieval`**: Decorator to track retrieval calls with provenance emission
- **`ProvenanceRegistry`**: Central registry for provenance sinks
- **`RetrievalProvenance`**: Immutable event with query, chunks, principal, session, outcome, timestamp
- **`ProvenanceSink`**: Abstract sink interface for provenance events
- **`CollectingProvenanceSink`**: In-memory collector for testing
- **`NullProvenanceSink`**: No-op sink (default)
- **`ProvenanceOutcome`**: Success/failure outcome enum
- Retrieval error classes: `RetrievalError`, `RetrievalDeclarationError`

## Features

### Per-Feature Documentation

- **[architecture/flow-trace.md](architecture/flow-trace.md)**: Complete flow diagram and runtime behavior
- **Security audits**: [audits/](audits/)
- **Code reviews**: [reviews/](reviews/)

## Common Patterns

### Basic Retrieval Tracing

```python
from monitoring_suite.rag import (
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

**Output (Python 3.12, monitoring-suite==0.1.1):**
```
Query: what is accessibility?
Chunks: ('chunk_a', 'chunk_b')
Principal: user_789
Outcome: success
```

### Custom Sink Implementation

Implement the `ProvenanceSink` protocol to emit to your observability platform:

```python
from monitoring_suite.rag import traced_retrieval, ProvenanceSink, RetrievalProvenance

class OpenTelemetrySink:
    def record(self, event: RetrievalProvenance) -> None:
        span = get_current_span()
        span.set_attribute("rag.query", event.query)
        span.set_attribute("rag.chunk_ids", event.chunk_ids)
        span.set_attribute("rag.principal_id", event.principal_id)
        span.set_attribute("rag.session_id", event.session_id)
        span.set_attribute("rag.outcome", event.outcome)

# Use with decorator
sink = OpenTelemetrySink()

@traced_retrieval(principal_id="user_123", session_id="sess_456", sink=sink)
def retrieve(query: str):
    return {"chunk_ids": ["c1"], "source_document_ids": ["d1"]}
```

### Class Decoration

Apply tracing to all public methods:

```python
from monitoring_suite.rag import traced_retrieval
from dataclasses import dataclass

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
from monitoring_suite.rag import traced_retrieval

@traced_retrieval(principal_id="user_123", session_id="sess_456")
async def async_retrieve(query: str):
    await asyncio.sleep(0.1)
    return {
        "chunk_ids": ["chunk_1"],
        "source_document_ids": ["doc_1"],
    }

result = asyncio.run(async_retrieve("query"))
```

## Integration with monitoring_suite.aspects

Compose with other aspects:

```python
from monitoring_suite.aspects import aspects, Logged
from monitoring_suite.rag import traced_retrieval

@aspects(
    Logged(event="rag.retrieve"),
)
@traced_retrieval(principal_id="user_123", session_id="sess_456")
def retrieve(query: str):
    return {"chunk_ids": ["c1"], "source_document_ids": ["d1"]}
```

## Next Steps

- Read the [main monitoring-suite README](../../README.md) for installation and examples
- Explore [architecture/flow-trace.md](architecture/flow-trace.md) for detailed flow diagrams
- Implement custom sinks for your observability platform
