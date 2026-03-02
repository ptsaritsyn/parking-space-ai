from cachetools import LRUCache

from app.core import _BaseRAGPipeline
from app.db import _BaseVectorDB
from app.llm import _BaseLLM
from app.llm.prompts import RAG_INFO_PROMPT


class RAGPipeline(_BaseRAGPipeline):
    def __init__(self, vector_db: _BaseVectorDB, llm: _BaseLLM):
        self.vector_db = vector_db
        self.llm = llm
        self._cache = LRUCache(maxsize=100)

    def _answer(self, query: str) -> str:
        if query in self._cache:
            return self._cache[query]

        docs = self.vector_db.search(query)
        context = " ".join([doc['content'] for doc in docs])
        prompt = RAG_INFO_PROMPT.format(context=context, question=query)
        response = self.llm.generate(prompt)
        self._cache[query] = response

        return response
