import pytest
from unittest.mock import MagicMock, patch
from app.agents.chat_agent import _BaseAgent, ChatAgent

# --- Tests for _BaseAgent ---

class DummyAgent(_BaseAgent):
    def _run(self, x):
        return x * 2

def test_baseagent_run_success():
    agent = DummyAgent()
    result = agent.run(3)
    assert result == 6

def test_baseagent_run_not_implemented():
    agent = _BaseAgent()
    with pytest.raises(NotImplementedError):
        agent.run()

def test_baseagent_run_exception_prints_and_raises(capfd):
    class ErrorAgent(_BaseAgent):
        def _run(self, *a, **k):
            raise ValueError("fail")
    agent = ErrorAgent()
    with pytest.raises(ValueError):
        agent.run()
    out, _ = capfd.readouterr()
    assert "Error in run" in out

# --- Tests for ChatAgent ---

@pytest.fixture
def mock_dependencies():
    rag = MagicMock()
    guard = MagicMock()
    llm = MagicMock()
    sql_db = MagicMock()
    return rag, guard, llm, sql_db

@patch("app.agents.chat_agent.ReservationGraph")
@patch("app.agents.chat_agent.MCPClientWrapper")
@patch("app.agents.chat_agent.MCPAsyncStdioClient")
def test_chatagent_run_reservation_success(mock_mcp_async, mock_mcp_wrapper, mock_graph_cls, mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"graph_state": {"response": "Reservation successful for John Smith ..."}}
    mock_graph_cls.return_value = mock_graph
    mock_mcp = MagicMock()
    mock_mcp.connect = MagicMock()
    mock_mcp_wrapper.return_value = mock_mcp

    agent = ChatAgent(rag, guard, llm, sql_db)
    result = agent.run("reserve")
    assert "Reservation successful" in result
    mock_graph.invoke.assert_called_once()
    mock_mcp.connect.assert_called_once()

@patch("app.agents.chat_agent.ReservationGraph")
@patch("app.agents.chat_agent.MCPClientWrapper")
@patch("app.agents.chat_agent.MCPAsyncStdioClient")
def test_chatagent_run_non_reservation_message(mock_mcp_async, mock_mcp_wrapper, mock_graph_cls, mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"graph_state": {"response": "safe answer"}}
    mock_graph_cls.return_value = mock_graph
    mock_mcp = MagicMock()
    mock_mcp.connect = MagicMock()
    mock_mcp_wrapper.return_value = mock_mcp

    agent = ChatAgent(rag, guard, llm, sql_db)
    result = agent.run("Hello, what is the weather?")
    assert result == "safe answer"
    mock_graph.invoke.assert_called_once()

@patch("app.agents.chat_agent.ReservationGraph")
@patch("app.agents.chat_agent.MCPClientWrapper")
@patch("app.agents.chat_agent.MCPAsyncStdioClient")
def test_chatagent_run_graph_returns_no_response(mock_mcp_async, mock_mcp_wrapper, mock_graph_cls, mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"graph_state": {}}
    mock_graph_cls.return_value = mock_graph
    mock_mcp = MagicMock()
    mock_mcp.connect = MagicMock()
    mock_mcp_wrapper.return_value = mock_mcp

    agent = ChatAgent(rag, guard, llm, sql_db)
    result = agent.run("something")
    assert result == ""
    mock_graph.invoke.assert_called_once()

def test_chatagent_check_llm_response_valid():
    agent = ChatAgent(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    data = {"foo": "bar"}
    json_str = '{"foo": "bar"}'
    assert agent._check_llm_response(json_str) == data

def test_chatagent_check_llm_response_invalid():
    agent = ChatAgent(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    with pytest.raises(Exception) as excinfo:
        agent._check_llm_response("not a json")
    assert "LLM JSON Parse Error" in str(excinfo.value)