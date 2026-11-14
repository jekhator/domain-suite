"""Tests for @traced_retrieval decorator."""

import asyncio
from dataclasses import dataclass

import pytest

from domain_rag.decorators.traced_retrieval.traced_retrieval_client import (
    traced_retrieval,
)
from domain_rag.errors.constants import retrieval as const
from domain_rag.errors.retrieval_errors import RetrievalDeclarationError
from domain_rag.services.constants import provenance as provenance_const
from domain_rag.services.provenance.provenance_client import CollectingProvenanceSink
from domain_rag.services.provenance.provenance_objects import ProvenanceOutcome
from domain_rag.services.registry.registry_client import ProvenanceRegistry


class TestTracedRetrievalOnCallable:
    """@traced_retrieval on functions and methods."""

    def test_traced_sync_callable_success(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on sync callable emits SUCCESS event."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str) -> list[str]:
            return ["chunk1", "chunk2"]

        result = retrieve("what is RAG?")

        assert result == ["chunk1", "chunk2"]
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "what is RAG?"
        assert collecting_sink.events[0].principal_id == "user_123"
        assert collecting_sink.events[0].session_id == "sess_456"
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.SUCCESS
        assert collecting_sink.events[0].duration_ms >= 0

    def test_traced_sync_callable_failure(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on sync callable emits FAILURE event on exception."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str) -> None:
            raise ValueError("retrieval failed")

        with pytest.raises(ValueError, match="retrieval failed"):
            retrieve("query")

        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "query"
        assert collecting_sink.events[0].principal_id == "user_123"
        assert collecting_sink.events[0].session_id == "sess_456"
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.FAILURE
        assert collecting_sink.events[0].is_failure

    def test_traced_async_callable_success(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on async callable emits SUCCESS event."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        async def retrieve(query: str) -> list[str]:
            await asyncio.sleep(0.01)
            return ["chunk1", "chunk2"]

        result = asyncio.run(retrieve("async query"))

        assert result == ["chunk1", "chunk2"]
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "async query"
        assert collecting_sink.events[0].principal_id == "user_123"
        assert collecting_sink.events[0].session_id == "sess_456"
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.SUCCESS

    def test_traced_async_callable_failure(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on async callable emits FAILURE event on exception."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        async def retrieve(query: str) -> None:
            await asyncio.sleep(0.01)
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            asyncio.run(retrieve("query"))

        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "query"
        assert collecting_sink.events[0].principal_id == "user_123"
        assert collecting_sink.events[0].session_id == "sess_456"
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.FAILURE

    def test_traced_with_registry_sink(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval resolves sink from registry when None."""
        ProvenanceRegistry.set_default_sink(collecting_sink)

        @traced_retrieval("user_123", "sess_456")
        def retrieve(query: str) -> list[str]:
            return ["chunk1"]

        result = retrieve("query")

        assert result == ["chunk1"]
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "query"

    def test_traced_with_dict_result(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval extracts chunk_ids and source_document_ids from dict result."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str) -> dict:
            return {
                "chunk_ids": ["c1", "c2"],
                "source_document_ids": ["d1", "d2"],
            }

        result = retrieve("query")

        assert result == {
            "chunk_ids": ["c1", "c2"],
            "source_document_ids": ["d1", "d2"],
        }
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].chunk_ids == ("c1", "c2")
        assert collecting_sink.events[0].source_document_ids == ("d1", "d2")

    def test_traced_with_args_and_kwargs(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval preserves function args and kwargs."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str, top_k: int = 5) -> list[str]:
            return [f"chunk_{i}" for i in range(top_k)]

        result = retrieve("test query", top_k=3)

        assert result == ["chunk_0", "chunk_1", "chunk_2"]
        assert len(collecting_sink.events) == 1


class TestTracedRetrievalOnClass:
    """@traced_retrieval on classes fans out to public methods."""

    def test_traced_class_public_methods(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on class fans out to public methods."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        @dataclass(frozen=True, slots=True)
        class RetrievalService:
            """Document retrieval service."""

            name: str

            def search(self, query: str) -> list[str]:
                return [f"result for {query}"]

            def rank(self, docs: list[str]) -> list[str]:
                return sorted(docs)

            def _private_method(self) -> str:
                return "private"

        service = RetrievalService(name="test")

        search_result = service.search("test")
        rank_result = service.rank(["a", "c", "b"])
        private_result = service._private_method()

        assert search_result == ["result for test"]
        assert rank_result == ["a", "b", "c"]
        assert private_result == "private"
        assert len(collecting_sink.events) == 2
        assert collecting_sink.events[0].query == "test"
        assert collecting_sink.events[1].query == "['a', 'c', 'b']"

    def test_traced_class_failure_on_method(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on class emits failure event from method exception."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        @dataclass(frozen=True, slots=True)
        class RetrievalService:
            """Test service."""

            fail: bool

            def retrieve(self, query: str) -> list[str]:
                if self.fail:
                    raise RuntimeError("retrieval failed")
                return ["chunk"]

        service = RetrievalService(fail=True)

        with pytest.raises(RuntimeError, match="retrieval failed"):
            service.retrieve("query")

        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "query"
        assert collecting_sink.events[0].principal_id == "user_123"
        assert collecting_sink.events[0].session_id == "sess_456"
        assert collecting_sink.events[0].is_failure

    def test_traced_empty_class_raises(self) -> None:
        """@traced_retrieval on class with no public methods raises."""
        with pytest.raises(RetrievalDeclarationError):

            @traced_retrieval("user_123", "sess_456")
            @dataclass(frozen=True, slots=True)
            class EmptyService:
                """Service with no public methods."""

                _private: str = ""

    def test_traced_invalid_target_raises(self) -> None:
        """@traced_retrieval on invalid target raises."""
        with pytest.raises(RetrievalDeclarationError):
            traced_retrieval("user_123", "sess_456")(42)  # type: ignore


class TestTracedRetrievalAsyncEdgeCases:
    """Async edge cases and special scenarios."""

    def test_traced_async_with_dict_result(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval async callable extracts chunk/source from dict."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        async def retrieve(query: str) -> dict:
            await asyncio.sleep(0.01)
            return {
                "chunk_ids": ["c1", "c2"],
                "source_document_ids": ["d1", "d2"],
            }

        asyncio.run(retrieve("async query"))

        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "async query"
        assert collecting_sink.events[0].chunk_ids == ("c1", "c2")
        assert collecting_sink.events[0].source_document_ids == ("d1", "d2")

    def test_traced_sync_with_dict_result(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval sync callable extracts chunk/source from dict."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str) -> dict:
            return {
                "chunk_ids": ["c1"],
                "source_document_ids": ["d1"],
            }

        result = retrieve("test query")

        assert result == {"chunk_ids": ["c1"], "source_document_ids": ["d1"]}
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "test query"
        assert collecting_sink.events[0].chunk_ids == ("c1",)
        assert collecting_sink.events[0].source_document_ids == ("d1",)

    def test_traced_async_with_kwargs_query(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval async with kwargs query parameter."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        async def retrieve(query: str) -> dict:
            await asyncio.sleep(0.01)
            return {
                "chunk_ids": ["c1"],
                "source_document_ids": ["d1"],
            }

        asyncio.run(retrieve(query="kwargs query"))

        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "kwargs query"

    def test_traced_async_method_success(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on async class method extracts query from second arg."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        @dataclass(frozen=True, slots=True)
        class AsyncRetrievalService:
            """Async retrieval service."""

            name: str

            async def search(self, query: str) -> dict:
                await asyncio.sleep(0.01)
                return {
                    "chunk_ids": ["async_c1"],
                    "source_document_ids": ["async_d1"],
                }

        service = AsyncRetrievalService(name="async_service")
        asyncio.run(service.search("async method query"))

        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "async method query"
        assert collecting_sink.events[0].chunk_ids == ("async_c1",)


class TestTracedRetrievalEdgeCases:
    """Edge cases and special scenarios."""

    def test_traced_preserves_function_name(self) -> None:
        """@traced_retrieval preserves original function name."""

        @traced_retrieval("user_123", "sess_456")
        def my_retrieval_function() -> str:
            return "result"

        assert my_retrieval_function.__name__ == "my_retrieval_function"

    def test_traced_with_return_value_and_exception(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """Multiple calls track separate success/failure events."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(should_fail: bool, query: str = "default") -> str:
            if should_fail:
                raise ValueError("intentional")
            return "ok"

        result1 = retrieve(False, query="q1")
        assert result1 == "ok"
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.SUCCESS

        with pytest.raises(ValueError):
            retrieve(True, query="q2")

        assert len(collecting_sink.events) == 2
        assert collecting_sink.events[1].outcome == ProvenanceOutcome.FAILURE

    def test_traced_class_with_classmethod(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on class with classmethod includes it in public methods."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        class RetrievalFactory:
            """Service with classmethod."""

            @classmethod
            def create(cls, query: str) -> "RetrievalFactory":
                """Factory method."""
                return cls()

        obj = RetrievalFactory.create("test query")
        assert obj is not None
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "test query"
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.SUCCESS

    def test_traced_class_with_staticmethod(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """@traced_retrieval on class with staticmethod includes it in public methods."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        class RetrievalUtils:
            """Service with staticmethod."""

            @staticmethod
            def helper(query: str) -> str:
                """Helper function."""
                return f"helper_{query}"

        result = RetrievalUtils.helper("test query")
        assert result == "helper_test query"
        assert len(collecting_sink.events) == 1
        assert collecting_sink.events[0].query == "test query"
        assert collecting_sink.events[0].outcome == ProvenanceOutcome.SUCCESS


class _RaisingProvenanceSink:
    """Sink whose record always fails."""

    def record(self, event: object) -> None:
        """Raise to simulate a failing audit backend."""
        raise RuntimeError("audit backend unavailable")


class TestTracedRetrievalResultPreservation:
    """Tracing reports outcomes without altering the wrapped call's result or exception."""

    def test_empty_principal_rejected_at_declaration(self) -> None:
        """An empty principal_id is rejected when the decorator is applied."""
        with pytest.raises(
            RetrievalDeclarationError, match=const.ERR_RETRIEVAL_EMPTY_PRINCIPAL
        ):
            traced_retrieval("", "sess_456")

    def test_empty_session_rejected_at_declaration(self) -> None:
        """An empty session_id is rejected when the decorator is applied."""
        with pytest.raises(
            RetrievalDeclarationError, match=const.ERR_RETRIEVAL_EMPTY_SESSION
        ):
            traced_retrieval("user_123", "")

    def test_zero_argument_call_uses_placeholder_query(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """A call with no arguments records the placeholder query instead of failing."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve() -> list[str]:
            return ["chunk1"]

        assert retrieve() == ["chunk1"]
        assert collecting_sink.events[0].query == provenance_const.NO_QUERY_PLACEHOLDER

    def test_empty_string_query_uses_placeholder(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """An empty query string records the placeholder and the result is unchanged."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str) -> list[str]:
            return ["chunk1"]

        assert retrieve("") == ["chunk1"]
        assert collecting_sink.events[0].query == provenance_const.NO_QUERY_PLACEHOLDER

    def test_non_iterable_ids_keep_result(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """Non-list id values produce empty id tuples and leave the result untouched."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        def retrieve(query: str) -> dict[str, object]:
            return {"chunk_ids": 7, "source_document_ids": None}

        assert retrieve("query") == {"chunk_ids": 7, "source_document_ids": None}
        assert collecting_sink.events[0].chunk_ids == ()
        assert collecting_sink.events[0].source_document_ids == ()

    def test_sink_failure_keeps_original_exception(self) -> None:
        """A failing sink adds a note to the call's exception and keeps its type."""

        @traced_retrieval("user_123", "sess_456", sink=_RaisingProvenanceSink())
        def retrieve(query: str) -> None:
            raise ValueError("retrieval error")

        with pytest.raises(ValueError, match="retrieval error") as caught:
            retrieve("query")

        assert any(
            provenance_const.NOTE_RECORDING_FAILED in note
            for note in caught.value.__notes__
        )

    def test_sink_failure_after_success_surfaces(self) -> None:
        """A failing sink after a successful call raises, so a missed audit record is loud."""

        @traced_retrieval("user_123", "sess_456", sink=_RaisingProvenanceSink())
        def retrieve(query: str) -> list[str]:
            return ["chunk1"]

        with pytest.raises(RuntimeError, match="audit backend unavailable"):
            retrieve("query")

    def test_classmethod_stays_callable_on_instances(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """Classmethods remain classmethods, so instance calls still bind the class."""

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        class Retriever:
            """Retriever with a classmethod."""

            label = "built"

            @classmethod
            def build(cls, query: str) -> str:
                """Return the class label."""
                return f"{cls.label}:{query}"

        assert Retriever().build("q") == "built:q"
        assert collecting_sink.events[0].query == "q"

    def test_inherited_methods_are_not_wrapped(
        self, collecting_sink: CollectingProvenanceSink
    ) -> None:
        """Only methods defined on the decorated class are traced, including overrides."""

        class Base:
            """Base with one method."""

            def search(self, query: str) -> str:
                """Return a value."""
                return "base"

        @traced_retrieval("user_123", "sess_456", sink=collecting_sink)
        class Child(Base):
            """Child that overrides the base method."""

            def search(self, query: str) -> str:
                """Return a value."""
                return "child"

        assert Child().search("q") == "child"
        assert len(collecting_sink.events) == 1
        assert Base().search("q") == "base"
        assert len(collecting_sink.events) == 1
