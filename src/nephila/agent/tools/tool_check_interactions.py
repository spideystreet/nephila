"""ANSM Thésaurus interaction lookup in ChromaDB idx_ansm_interaction_v1."""
import chromadb
from langchain_core.tools import tool

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function


@tool
def check_interactions(substance: str) -> str:
    """
    Check ANSM Thésaurus for drug interactions involving a substance or drug class.
    Returns interactions with their constraint level.
    ALWAYS call this before any drug recommendation.
    Constraint levels: Contre-indication > Association déconseillée > Précaution d'emploi > A prendre en compte
    """
    settings = PipelineSettings()
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    ef = get_embedding_function(settings.embedding_model)

    collection = client.get_collection("idx_ansm_interaction_v1", embedding_function=ef)
    results = collection.query(
        query_texts=[substance],
        n_results=10,
        include=["documents", "metadatas"],
    )

    if not results["documents"][0]:
        return f"No interactions found for '{substance}' in ANSM Thésaurus."

    lines = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        lines.append(
            f"[{meta['niveau_contrainte']}] {meta['substance_a']} + {meta['substance_b']}\n{doc}"
        )
    return "\n\n".join(lines)
