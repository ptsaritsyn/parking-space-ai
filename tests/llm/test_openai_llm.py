import pytest
from unittest.mock import MagicMock, patch
from app.llm.openai_llm import _BaseLLM, OpenAIClient

# --- Tests for _BaseLLM ---

class DummyLLM(_BaseLLM):
    def _generate(self, prompt):
        return prompt[::-1]

def test_basellm_generate_success():
    llm = DummyLLM()
    result = llm.generate("hello")
    assert result == "olleh"


def test_basellm_not_implemented():
    llm = _BaseLLM()
    with pytest.raises(NotImplementedError):
        llm.generate("test")


def test_basellm_exception_prints_and_raises(capfd):
    class ErrorLLM(_BaseLLM):
        def _generate(self, *a, **k):
            raise ValueError("fail")
    llm = ErrorLLM()
    with pytest.raises(ValueError):
        llm.generate("test")
    out, _ = capfd.readouterr()
    assert "Error in generate" in out

# --- Tests for OpenAIClient ---

@pytest.fixture
def mock_openai_client():
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_completions = MagicMock()
    mock_create = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "mocked response"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response
    mock_completions.create = mock_create
    mock_chat.completions = mock_completions
    mock_client.chat = mock_chat
    return mock_client

@patch("app.llm.openai_llm.openai.OpenAI")
def test_openaiclient_generate_success(mock_openai_cls, mock_openai_client):
    mock_openai_cls.return_value = mock_openai_client
    client = OpenAIClient(api_key="fake-key")
    result = client.generate("test prompt")
    assert result == "mocked response"
    mock_openai_client.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test prompt"}]
    )


@patch("app.llm.openai_llm.OpenAIClient")
def test_openaiclient_generate_exception(mock_openai_cls, mock_openai_client):
    mock_openai_cls.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.side_effect = Exception("fail")
    client = OpenAIClient(api_key="fake-key")
    with pytest.raises(Exception):
        client.generate("test prompt")
