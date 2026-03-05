import pytest
from dotenv import load_dotenv

from app.agents.chat_agent import ChatAgent
from app.core.guard_rails import CarNumberPIIGuard
from app.core.rag import RAGPipeline
from app.db.pinecone_db import PineconeVectorDB
from app.db.sqlite_db import SQLiteDB
from app.ingest.ingest_static import ingest_static_data
from app.llm.openai_llm import OpenAIClient


@pytest.mark.integration
def test_chatagent_integration_real_stack():
    load_dotenv()

    vector_db = PineconeVectorDB()
    ingest_static_data(vector_db)
    sql_db = SQLiteDB()
    llm = OpenAIClient()
    rag = RAGPipeline(vector_db=vector_db, llm=llm)
    guard = CarNumberPIIGuard()
    agent = ChatAgent(rag, guard, llm, sql_db)

    message = "Please reserve a spot for John Smith AA1234BB 2026-12-19T10:10:00 2026-12-19T11:10:00 reserve"
    result = agent.run(message)

    print("Integration test result:", result)
    assert (
        "Reservation successful" in result
        or "no available spots" in result
        or "already exist" in result
        or "refused by the administrator" in result
    )
