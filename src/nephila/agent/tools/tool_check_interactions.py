"""ANSM Thésaurus interaction lookup — dual SQL ILIKE + ChromaDB vector search."""

import re
import unicodedata

import chromadb
from langchain_core.tools import tool
from sqlalchemy import create_engine, text

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
    Check ANSM Thésaurus for the interaction between two substances or drug classes.

    The ANSM Thésaurus indexes interactions by pharmacological class names, not individual
    drug names. This tool automatically discovers the correct ANSM class name for each
    substance via semantic search, so you can pass individual drug names directly
    (e.g. 'warfarine', 'aspirine', 'ciprofloxacine').

    Returns the interaction with its constraint level.
    ALWAYS call this for every drug pair before any recommendation.
    Constraint levels: Contre-indication > Association déconseillée
    > Précaution d'emploi > A prendre en compte
    """
    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)

    seen: set[frozenset[str]] = set()
    sql_lines: list[str] = []

    # Step 1: SQL ILIKE — search with both original and normalized (unaccented) forms
    conditions: list[str] = []
    params: dict[str, str] = {}
    idx = 0
    for va, vb in [
        (substance_a, substance_b),
        (_normalize(substance_a), _normalize(substance_b)),
    ]:
        pa, pb = f"a{idx}", f"b{idx}"
        params[pa] = f"%{va}%"
        params[pb] = f"%{vb}%"
        conditions.append(f"(substance_a ILIKE :{pa} AND substance_b ILIKE :{pb})")
        conditions.append(f"(substance_a ILIKE :{pb} AND substance_b ILIKE :{pa})")
        idx += 1

    where_clause = " OR ".join(conditions)
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT substance_a, substance_b, niveau_contrainte, nature_risque, conduite_a_tenir
                FROM silver.silver_ansm__interaction
                WHERE {where_clause}
                ORDER BY
                    CASE niveau_contrainte
                        WHEN 'Contre-indication' THEN 1
                        WHEN 'Association déconseillée' THEN 2
                        WHEN 'Précaution d''emploi' THEN 3
                        ELSE 4
                    END
                LIMIT 10
            """),
            params,
        ).fetchall()

    for row in rows:
        pair = frozenset([row[0], row[1]])
        if pair not in seen:
            seen.add(pair)
            parts = [
                f"Interaction: {row[0]} + {row[1]}",
                f"Niveau de contrainte: {row[2]}",
            ]
            if row[3]:
                parts.append(f"Nature du risque: {row[3]}")
            if row[4]:
                parts.append(f"Conduite à tenir: {row[4]}")
            sql_lines.append(f"[{row[2]}] {row[0]} + {row[1]}\n{'. '.join(parts)}")

    # Step 2: vector search — semantic fallback when class names are unknown
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    ef = get_embedding_function(settings.embedding_model)
    collection = client.get_collection(
        "idx_ansm_interaction_v1", embedding_function=ef  # type: ignore[arg-type]
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
        # Require lexical overlap: both returned substances must relate to a query substance.
        # This prevents false positives where a semantically similar but different drug
        # (e.g. flucloxacilline for amoxicilline) contaminates the result.
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
    if not all_results:
        return (
            f"No interaction found between '{substance_a}' and '{substance_b}' in ANSM Thésaurus. "
            "Try using the ANSM pharmacological class names (e.g. 'ANTIVITAMINES K', 'STATINES')."
        )

    return "\n\n".join(all_results)
