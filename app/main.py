from app.agents.chat_agent import ChatAgent
from app.core.guard_rails import CarNumberPIIGuard
from app.core.rag import RAGPipeline
from app.db.pinecone_db import PineconeVectorDB
from app.db.sqlite_db import SQLiteDB
from app.gui.streamlit_gui import ChatGUI
from dotenv import load_dotenv

from app.ingest.ingest_static import ingest_static_data
from app.llm.openai_llm import OpenAIClient

load_dotenv()

vector_db = PineconeVectorDB()
ingest_static_data(vector_db)
sql_db = SQLiteDB()
llm = OpenAIClient()
rag = RAGPipeline(vector_db=vector_db, llm=llm)
guard = CarNumberPIIGuard()
agent = ChatAgent(rag, guard, llm, sql_db)

def main():
    gui = ChatGUI(agent)
    gui.run()

if __name__ == "__main__":
    main()
