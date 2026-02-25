"""
Gold layer — Vector embeddings stored in ChromaDB.
Metadata filtering by CIS code (drug) and CIP13 code (presentation/box).
"""
from dagster import asset


@asset(group_name="gold", deps=["silver_bdpm"])
def gold_embeddings() -> None:
    """Generate and index embeddings into ChromaDB."""
    ...
