import pytest
from unittest.mock import MagicMock, patch
from app.core.rag import _BaseRAGPipeline, RAGPipeline

# --- Tests for _BaseRAGPipeline ---

class DummyRAG(_BaseRAGPipeline):
    def _answer(self, x):
        return x + "!"

def test_baseragpipeline_answer_success():
    rag = DummyRAG()
    result = rag.answer("hello")
    assert result == "hello!"


def test_baseragpipeline_answer_not_implemented():
    rag = _BaseRAGPipeline()
    with pytest.raises(NotImplementedError):
        rag.answer()


def test_baseragpipeline_answer_exception_prints_and_raises(capfd):
    class ErrorRAG(_BaseRAGPipeline):
        def _answer(self, *a, **k):
            raise ValueError("fail")
    rag = ErrorRAG()
    with pytest.raises(ValueError):
        rag.answer()
    out, _ = capfd.readouterr()
    assert "Error in answer" in out

# --- Tests for RAGPipeline ---

@pytest.fixture
def mock_vector_llm():
    vector_db = MagicMock()
    llm = MagicMock()
    return vector_db, llm


@patch("app.core.rag.RAG_INFO_PROMPT", "Context: {context} Q: {question}")
def test_ragpipeline_answer_success(mock_vector_llm):
    vector_db, llm = mock_vector_llm
    vector_db.search.return_value = [
        {'content': 'doc1'}, {'content': 'doc2'}
    ]

    llm.generate.return_value = "final answer"
    rag = RAGPipeline(vector_db, llm)
    query = "What is AI?"
    result = rag.answer(query)
    assert result == "final answer"

    vector_db.search.assert_called_once_with(query)
    llm.generate.assert_called_once_with("Context: doc1 doc2 Q: What is AI?")


@patch("app.core.rag.RAG_INFO_PROMPT", "Context: {context} Q: {question}")
def test_ragpipeline_answer_empty_docs(mock_vector_llm):
    vector_db, llm = mock_vector_llm
    vector_db.search.return_value = []
    llm.generate.return_value = "no context answer"
    rag = RAGPipeline(vector_db, llm)
    query = "Empty?"
    result = rag.answer(query)
    assert result == "no context answer"

    llm.generate.assert_called_once_with("Context:  Q: Empty?")


def test_ragpipeline_answer_exception_propagation(mock_vector_llm):
    vector_db, llm = mock_vector_llm
    vector_db.search.side_effect = Exception("DB error")
    rag = RAGPipeline(vector_db, llm)
    with pytest.raises(Exception):
        rag.answer("fail")


@patch("app.core.rag.RAG_INFO_PROMPT", "Context: {context} Q: {question}")
def test_ragpipeline_cache_hit_and_miss():
    vector_db = MagicMock()
    llm = MagicMock()
    rag = RAGPipeline(vector_db, llm)
    query = "What is cache?"

    vector_db.search.return_value = [{'content': 'doc1'}]
    llm.generate.return_value = "answer1"
    result1 = rag.answer(query)
    assert result1 == "answer1"

    vector_db.search.assert_called_once_with(query)
    llm.generate.assert_called_once_with("Context: doc1 Q: What is cache?")
    rag._cache[query] = "cached answer"

    vector_db.search.reset_mock()
    llm.generate.reset_mock()

    result2 = rag.answer(query)
    assert result2 == "cached answer"

    vector_db.search.assert_not_called()
    llm.generate.assert_not_called()


@patch("app.core.rag.RAG_INFO_PROMPT", "Context: {context} Q: {question}")
def test_ragpipeline_cache_isolation():
    vector_db = MagicMock()
    llm = MagicMock()
    rag = RAGPipeline(vector_db, llm)
    rag._cache["q1"] = "a1"
    rag._cache["q2"] = "a2"

    assert rag.answer("q1") == "a1"
    assert rag.answer("q2") == "a2"

    vector_db.search.return_value = [{'content': 'docX'}]
    llm.generate.return_value = "aX"
    assert rag.answer("qX") == "aX"

    vector_db.search.assert_called_once_with("qX")
    llm.generate.assert_called_once_with("Context: docX Q: qX")