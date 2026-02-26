import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from . import _BaseVectorDB


class PineconeVectorDB(_BaseVectorDB):
    def __init__(self, index_name=None, dimension=384):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = index_name or os.getenv("PINECONE_INDEX", "parking-static")
        self.dimension = dimension
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.pc = Pinecone(api_key=self.api_key)

        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        self.index = self.pc.Index(self.index_name)

    def _add_documents(self, docs):
        contents = [doc["content"] for doc in docs]
        embeddings = self.embedding_model.encode(contents)
        vectors = []
        for i, (content, emb) in enumerate(zip(contents, embeddings)):
            vectors.append({
                "id": str(i),
                "values": emb.tolist(),
                "metadata": {"content": content}
            })
        self.index.upsert(vectors=vectors)

    def _search(self, query, top_k=5):
        embedding = self.embedding_model.encode([query])
        results = self.index.query(
            vector=embedding.tolist()[0],
            top_k=top_k,
            include_metadata=True
        )
        hits = []
        for match in results["matches"]:
            hits.append({"content": match["metadata"]["content"]})
        return hits
