import json
from pathlib import Path
import chromadb

from src.retrieval.embedder import LocalEmbedder


class RecommendationTool:
    def __init__(
        self,
        resources_path: str = "data/recommendations/resources.json",
        persist_dir: str = "data/chroma_recommendations",
        collection_name: str = "recommendation_chunks",
    ) -> None:
        self.resources_path = Path(resources_path)
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedder = LocalEmbedder()

    def build_index(self) -> None:
        client = chromadb.PersistentClient(path=self.persist_dir)

        existing = [c.name for c in client.list_collections()]
        if self.collection_name in existing:
            client.delete_collection(self.collection_name)

        collection = client.create_collection(name=self.collection_name)

        resources = json.loads(self.resources_path.read_text(encoding="utf-8"))

        documents = []
        metadatas = []
        ids = []

        for item in resources:
            topics = ", ".join(item.get("topics", []))
            doc = (
                f"Title: {item.get('title', '')}\n"
                f"Type: {item.get('type', '')}\n"
                f"Topics: {topics}\n"
                f"Summary: {item.get('summary', '')}"
            )

            documents.append(doc)
            metadatas.append(
                {
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "type": item.get("type", ""),
                    "file": item.get("file", ""),
                    "topics": topics,
                    "source_type": "recommendation",
                }
            )
            ids.append(item.get("id", f"rec_{len(ids)}"))

        if not documents:
            raise ValueError("No recommendation resources found to index.")

        embeddings = self.embedder.encode(documents)

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        print(f"Indexed {len(documents)} recommendation items into '{self.collection_name}'.")

    def search(self, query: str, top_k: int = 3) -> dict:
        client = chromadb.PersistentClient(path=self.persist_dir)
        collection = client.get_collection(name=self.collection_name)

        query_embedding = self.embedder.encode([query])[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return results