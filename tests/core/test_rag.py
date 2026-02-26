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

@patch("app.core.rag.INFO_PROMPT", "Context: {context} Q: {question}")
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


@patch("app.core.rag.INFO_PROMPT", "Context: {context} Q: {question}")
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
