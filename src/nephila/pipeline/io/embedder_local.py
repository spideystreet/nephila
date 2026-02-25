"""
Local embedding function for ChromaDB using sentence-transformers (HuggingFace).
Model is downloaded and cached locally on first use — zero API cost, HDS-compatible.
"""
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


def get_embedding_function(model_name: str) -> SentenceTransformerEmbeddingFunction:
    """
    Return a ChromaDB-compatible embedding function backed by a local HuggingFace model.
    Default: intfloat/multilingual-e5-base (multilingual, optimized for retrieval).
    """
    return SentenceTransformerEmbeddingFunction(model_name=model_name)
