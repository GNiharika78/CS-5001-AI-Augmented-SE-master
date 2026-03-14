from sentence_transformers import SentenceTransformer


class LocalEmbedder:
    _model = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        if LocalEmbedder._model is None:
            LocalEmbedder._model = SentenceTransformer(model_name)
        self.model = LocalEmbedder._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()