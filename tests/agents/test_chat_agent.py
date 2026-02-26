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

@patch("app.agents.chat_agent.RESERVATION_EXTRACTION_PROMPT", "Prompt: {message}")
def test_chatagent_reservation_success(mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    llm.generate.return_value = (
        '{"name": "John", "surname": "Smith", "car_number": "AA1234BB", '
        '"reservation_from": "2026-03-19T10:10:00", "reservation_to": "2026-03-19T10:11:00"}'
    )

    spot = MagicMock(id=1, number=42)
    sql_db.get.side_effect = [spot, None]
    user = MagicMock(id=2)
    sql_db.add.side_effect = [user, MagicMock()]
    agent = ChatAgent(rag, guard, llm, sql_db)
    message = "Please reserve a spot for John Smith AA1234BB 2026-02-19T10:10:00 2026-02-19T10:11:00"
    result = agent.run(message)
    assert "Reservation successful" in result


@patch("app.agents.chat_agent.RESERVATION_EXTRACTION_PROMPT", "Prompt: {message}")
def test_chatagent_reservation_no_spots(mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    llm.generate.return_value = (
        '{"name": "John", "surname": "Smith", "car_number": "AA1234BB", '
        '"reservation_from": "2026-03-19T10:10:00", "reservation_to": "2026-03-19T10:11:00"}'
    )
    sql_db.get.side_effect = [None]
    agent = ChatAgent(rag, guard, llm, sql_db)
    message = "reserve"
    result = agent.run(message)
    assert "no available spots" in result


@patch("app.agents.chat_agent.RESERVATION_EXTRACTION_PROMPT", "Prompt: {message}")
def test_chatagent_reservation_user_exists(mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    llm.generate.return_value = (
        '{"name": "John", "surname": "Smith", "car_number": "AA1234BB", '
        '"reservation_from": "2026-03-19T10:10:00", "reservation_to": "2026-03-19T10:11:00"}'
    )
    spot = MagicMock(id=1, number=42)
    user = MagicMock(id=2)
    sql_db.get.side_effect = [spot, user]
    agent = ChatAgent(rag, guard, llm, sql_db)
    message = "reserve"
    result = agent.run(message)
    assert "already exist" in result


@patch("app.agents.chat_agent.RESERVATION_EXTRACTION_PROMPT", "Prompt: {message}")
def test_chatagent_reservation_invalid_json(mock_dependencies, capfd):
    rag, guard, llm, sql_db = mock_dependencies
    llm.generate.return_value = "not a json"
    agent = ChatAgent(rag, guard, llm, sql_db)
    message = "reserve"

    with pytest.raises(Exception):
        agent.run(message)

    out, _ = capfd.readouterr()
    assert "LLM JSON Parse Error" in out


@patch("app.agents.chat_agent.RESERVATION_EXTRACTION_PROMPT", "Prompt: {message}")
def test_chatagent_reservation_validation_error(mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    llm.generate.return_value = '{"name": "John"}'
    agent = ChatAgent(rag, guard, llm, sql_db)
    message = "reserve"
    result = agent.run(message)
    assert "Please fill all necessary information" in result


def test_chatagent_non_reservation_message(mock_dependencies):
    rag, guard, llm, sql_db = mock_dependencies
    rag.answer.return_value = "raw answer"
    guard.filter.return_value = "safe answer"
    agent = ChatAgent(rag, guard, llm, sql_db)
    message = "Hello, what is the weather?"
    result = agent.run(message)
    assert result == "safe answer"
