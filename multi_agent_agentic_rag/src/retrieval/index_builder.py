from pathlib import Path
import chromadb

from src.retrieval.chunker import read_text_file, chunk_text
from src.retrieval.embedder import LocalEmbedder


class PaperIndexBuilder:
    def __init__(
        self,
        papers_dir: str = "data/papers",
        persist_dir: str = "data/chroma_papers",
        collection_name: str = "paper_chunks",
    ) -> None:
        self.papers_dir = Path(papers_dir)
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedder = LocalEmbedder()

    def build(self) -> None:
        client = chromadb.PersistentClient(path=self.persist_dir)

        existing = [c.name for c in client.list_collections()]
        if self.collection_name in existing:
            client.delete_collection(self.collection_name)

        collection = client.create_collection(name=self.collection_name)

        documents = []
        metadatas = []
        ids = []

        for file_path in sorted(self.papers_dir.glob("*.txt")):
            raw_text = read_text_file(str(file_path))
            chunks = chunk_text(raw_text, chunk_size=500, overlap=80)

            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append(
                    {
                        "file_name": file_path.name,
                        "chunk_index": idx,
                        "source_type": "paper",
                    }
                )
                ids.append(f"{file_path.stem}_{idx}")

        if not documents:
            raise ValueError("No paper documents found to index.")

        embeddings = self.embedder.encode(documents)

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        print(f"Indexed {len(documents)} chunks into collection '{self.collection_name}'.")