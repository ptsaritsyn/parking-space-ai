import pytest
from unittest.mock import MagicMock, patch
from app.gui.streamlit_gui import _BaseGUI, ChatGUI

# --- Tests for _BaseGUI ---

class DummyGUI(_BaseGUI):
    def _run(self, x):
        return x.upper()


def test_basegui_run_success():
    gui = DummyGUI()
    result = gui.run("hello")
    assert result == "HELLO"


def test_basegui_not_implemented():
    gui = _BaseGUI()
    with pytest.raises(NotImplementedError):
        gui.run("test")


def test_basegui_exception_prints_and_raises(capfd):
    class ErrorGUI(_BaseGUI):
        def _run(self, *a, **k):
            raise ValueError("fail")
    gui = ErrorGUI()
    with pytest.raises(ValueError):
        gui.run("test")
    out, _ = capfd.readouterr()
    assert "Error in run" in out


class SessionStateMock(dict):
    def __getattr__(self, name):
        return self[name]
    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.run.return_value = "mocked response"
    return agent


@patch("app.gui.streamlit_gui.st")
def test_chatgui_run_remove_chat(mock_st, mock_agent):
    mock_st.title = MagicMock()
    mock_st.button.side_effect = lambda label: label == "🗑️ Remove Chat"

    def rerun_side_effect():
        raise SystemExit

    mock_st.rerun = MagicMock(side_effect=rerun_side_effect)
    mock_st.session_state = SessionStateMock()
    gui = ChatGUI(mock_agent)

    with pytest.raises(SystemExit):
        gui._run()

    assert mock_st.session_state["chat_history"] == []
    mock_st.rerun.assert_called_once()


@patch("app.gui.streamlit_gui.st")
def test_chatgui_run_shows_history_and_handles_input(mock_st, mock_agent):
    mock_st.title = MagicMock()
    mock_st.button.return_value = False
    mock_st.session_state = SessionStateMock(chat_history=[("Hi!", True), ("Hello!", False)])
    mock_chat_message_ctx = MagicMock()
    mock_chat_message_ctx.__enter__.return_value = None
    mock_chat_message_ctx.__exit__.return_value = None
    mock_st.chat_message.return_value = mock_chat_message_ctx
    mock_st.markdown = MagicMock()
    mock_st.chat_input.return_value = None
    gui = ChatGUI(mock_agent)
    gui._run()
    assert mock_st.markdown.call_count == 2


@patch("app.gui.streamlit_gui.st")
def test_chatgui_run_user_message_flow(mock_st, mock_agent):
    mock_st.title = MagicMock()
    mock_st.button.return_value = False
    mock_st.session_state = SessionStateMock()
    mock_chat_message_ctx = MagicMock()
    mock_chat_message_ctx.__enter__.return_value = None
    mock_chat_message_ctx.__exit__.return_value = None
    mock_st.chat_message.return_value = mock_chat_message_ctx
    mock_st.markdown = MagicMock()
    mock_st.chat_input.return_value = "How to park?"
    gui = ChatGUI(mock_agent)
    gui._run()

    assert mock_st.session_state["chat_history"][0] == ("How to park?", True)
    assert mock_st.session_state["chat_history"][1] == ("mocked response", False)

    mock_agent.run.assert_called_once_with("How to park?")
    assert mock_st.markdown.call_count >= 2


def test_chatgui_string_to_stream(mock_agent):
    gui = ChatGUI(mock_agent)
    result = list(gui.string_to_stream("abc"))
    assert result == ["a", "b", "c"]
