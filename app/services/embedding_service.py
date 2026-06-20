from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def embed(
        self,
        text: str
    ) -> list[float]:

        if not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        embedding = self.model.encode(
            text
        )

        return embedding.tolist()

    def embed_batch(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        if not texts:
            raise ValueError(
                "Texts list cannot be empty."
            )

        embeddings = self.model.encode(
            texts
        )

        return embeddings.tolist()


embedding_service = EmbeddingService()