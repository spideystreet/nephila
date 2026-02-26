"""Semantic drug search in ChromaDB idx_bdpm_medicament_v1."""

import chromadb
from langchain_core.tools import tool

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function


@tool
def search_drug(query: str) -> str:
    """
    Search for drug information by name, active substance, or description.
    Returns up to 5 relevant drugs with their CIS code, denomination, and key metadata.
    """
    settings = PipelineSettings()
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    ef = get_embedding_function(settings.embedding_model)

    collection = client.get_collection("idx_bdpm_medicament_v1", embedding_function=ef)  # type: ignore[arg-type]
    results = collection.query(
        query_texts=[query],
        n_results=5,
        include=["documents", "metadatas"],
    )

    docs = (results["documents"] or [[]])[0]
    metas = (results["metadatas"] or [[]])[0]

    if not docs:
        return f"No drugs found for query: {query!r}"

    lines = []
    for doc, meta in zip(docs, metas):
        lines.append(f"CIS {meta['cis']}: {doc}")
    return "\n\n".join(lines)
