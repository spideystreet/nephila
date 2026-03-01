"""ANSM Thésaurus interaction lookup — dual SQL ILIKE + ChromaDB vector search."""

import re
import unicodedata

import chromadb
from langchain_core.tools import tool

from nephila.agent.queries import find_interactions
from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function


def _normalize(name: str) -> str:
    """Lowercase and strip accents for lexical matching."""
    nfkd = unicodedata.normalize("NFKD", name)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


def _substance_matches_query(substance: str, query_a: str, query_b: str) -> bool:
    """Return True if substance shares at least one word token with query_a or query_b."""
    s_tokens = set(re.split(r"[\s\-\+]+", _normalize(substance)))
    for q in (query_a, query_b):
        q_tokens = set(re.split(r"[\s\-\+]+", _normalize(q)))
        if s_tokens & q_tokens:
            return True
    return False


@tool
def check_interactions(substance_a: str, substance_b: str) -> str:
    """
    Check ANSM Thésaurus for the interaction between two substances.

    Pass individual DCI names — the tool resolves them automatically to ANSM
    pharmacological class names when a mapping exists.

    Returns the interaction with its constraint level.
    ALWAYS call this before any drug recommendation.
    Constraint levels: Contre-indication > Association déconseillée
    > Précaution d'emploi > A prendre en compte
    """
    # Step 1: SQL ILIKE via queries module (resolves ANSM classes internally)
    interaction_rows = find_interactions(substance_a, substance_b)

    seen: set[frozenset[str]] = set()
    sql_lines: list[str] = []

    for row in interaction_rows:
        pair = frozenset([row.substance_a, row.substance_b])
        if pair not in seen:
            seen.add(pair)
            parts = [
                f"Interaction: {row.substance_a} + {row.substance_b}",
                f"Niveau de contrainte: {row.niveau_contrainte}",
            ]
            if row.nature_risque:
                parts.append(f"Nature du risque: {row.nature_risque}")
            if row.conduite_a_tenir:
                parts.append(f"Conduite à tenir: {row.conduite_a_tenir}")
            sql_lines.append(
                f"[{row.niveau_contrainte}] {row.substance_a} + {row.substance_b}\n"
                f"{'. '.join(parts)}"
            )

    # Step 2: vector search — semantic fallback when class names are unknown
    settings = PipelineSettings()
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    ef = get_embedding_function(settings.embedding_model)
    collection = client.get_collection(
        "idx_ansm_interaction_v1",
        embedding_function=ef,  # type: ignore[arg-type]
    )

    vector_results = collection.query(
        query_texts=[f"{substance_a} {substance_b}"],
        n_results=3,
        include=["documents", "metadatas"],
    )

    vector_lines: list[str] = []
    docs = (vector_results["documents"] or [[]])[0]
    metas = (vector_results["metadatas"] or [[]])[0]
    for doc, meta in zip(docs, metas):
        sa, sb = str(meta["substance_a"]), str(meta["substance_b"])
        if not (
            _substance_matches_query(sa, substance_a, substance_b)
            and _substance_matches_query(sb, substance_a, substance_b)
        ):
            continue
        pair = frozenset([sa, sb])
        if pair not in seen:
            seen.add(pair)
            vector_lines.append(f"[{meta['niveau_contrainte']}] {sa} + {sb}\n{doc}")

    all_results = sql_lines + vector_lines
    if all_results:
        return "\n\n".join(all_results)

    return (
        f"Aucune interaction trouvée dans le thésaurus ANSM entre '{substance_a}' "
        f"et '{substance_b}'. "
        "Répondre uniquement : données ANSM insuffisantes pour conclure."
    )
