"""
Gold layer — Vector embeddings dans ChromaDB.
Metadata-filtering par code CIS (spécialité) et CIP13 (présentation).
"""
from dagster import asset


@asset(group_name="gold", deps=["silver_bdpm"])
def gold_embeddings() -> None:
    """Génération et indexation des embeddings dans ChromaDB."""
    ...
