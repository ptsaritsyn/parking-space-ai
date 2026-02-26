from app.core import _BaseRAGPipeline
from app.db import _BaseVectorDB
from app.llm import _BaseLLM
from app.llm.prompts import INFO_PROMPT


class RAGPipeline(_BaseRAGPipeline):
    def __init__(self, vector_db: _BaseVectorDB, llm: _BaseLLM):
        self.vector_db = vector_db
        self.llm = llm

    def _answer(self, query: str) -> str:
        docs = self.vector_db.search(query)
        context = " ".join([doc['content'] for doc in docs])
        prompt = INFO_PROMPT.format(context=context, question=query)
        return self.llm.generate(prompt)
