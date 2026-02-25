"""ChromaDB EmbeddingFunction backed by OpenRouter (OpenAI-compatible API)."""
import chromadb
from openai import OpenAI


class OpenRouterEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self, api_key: str, base_url: str, model: str, batch_size: int = 100) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._batch_size = batch_size

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        embeddings: chromadb.Embeddings = []
        for i in range(0, len(input), self._batch_size):
            batch = input[i : i + self._batch_size]
            response = self._client.embeddings.create(input=batch, model=self._model)
            embeddings.extend([item.embedding for item in response.data])
        return embeddings
