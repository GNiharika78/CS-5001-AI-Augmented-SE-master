import chromadb

from src.retrieval.embedder import LocalEmbedder


class VectorSearchTool:
    def __init__(
        self,
        persist_dir: str = "data/chroma_papers",
        collection_name: str = "paper_chunks",
    ) -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_collection(name=collection_name)
        self.embedder = LocalEmbedder()

    def search(self, query: str, top_k: int = 3) -> dict:
        query_embedding = self.embedder.encode([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return results