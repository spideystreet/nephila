"""
Gold layer — Vector embeddings stored in ChromaDB.
Index naming: idx_<source>_<content>_<model_version>
Metadata filtering by CIS (drug specialty) and CIP13 (presentation/box).
"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dagster import AssetExecutionContext, AssetKey, asset
from sqlalchemy import create_engine

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.builder_documents import (
    build_interaction_documents,
    build_medicament_documents,
)
from nephila.pipeline.io.embedder_local import get_embedding_function

BATCH_SIZE = 100


@asset(
    group_name="gold",
    deps=[
        AssetKey(["silver", "silver_bdpm__medicament"]),
        AssetKey(["silver", "silver_bdpm__composition"]),
        AssetKey(["silver", "silver_ansm__interaction"]),
    ],
)
def gold_embeddings(context: AssetExecutionContext) -> None:
    """
    Build and upsert ChromaDB collections from Silver tables.
    Collections: idx_bdpm_medicament_v1, idx_ansm_interaction_v1
    """
    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)

    ef = get_embedding_function(settings.embedding_model)

    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)

    med_count = _upsert_collection(
        client=client,
        ef=ef,
        name="idx_bdpm_medicament_v1",
        builder=lambda: build_medicament_documents(engine),
        context=context,
    )

    int_count = _upsert_collection(
        client=client,
        ef=ef,
        name="idx_ansm_interaction_v1",
        builder=lambda: build_interaction_documents(engine),
        context=context,
    )

    context.add_output_metadata(
        {
            "idx_bdpm_medicament_v1": med_count,
            "idx_ansm_interaction_v1": int_count,
        }
    )


def _upsert_collection(
    client: chromadb.HttpClient,
    ef: SentenceTransformerEmbeddingFunction,
    name: str,
    builder: object,
    context: AssetExecutionContext,
) -> int:
    """Build documents and upsert them into a ChromaDB collection in batches."""
    collection = client.get_or_create_collection(name=name, embedding_function=ef)

    ids, documents, metadatas = builder()  # type: ignore[operator]
    total = len(ids)

    for i in range(0, total, BATCH_SIZE):
        collection.upsert(
            ids=ids[i : i + BATCH_SIZE],
            documents=documents[i : i + BATCH_SIZE],
            metadatas=metadatas[i : i + BATCH_SIZE],
        )
        context.log.info(f"[gold] {name} — upserted {min(i + BATCH_SIZE, total)}/{total}")

    return total
