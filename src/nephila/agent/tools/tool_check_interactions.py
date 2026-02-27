"""ANSM Thésaurus interaction lookup — dual SQL ILIKE + ChromaDB vector search."""

from collections import Counter

import chromadb
from langchain_core.tools import tool
from sqlalchemy import create_engine, text

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function

_SQL = """
    SELECT substance_a, substance_b, niveau_contrainte, nature_risque, conduite_a_tenir
    FROM silver.silver_ansm__interaction
    WHERE (substance_a ILIKE :pattern_a AND substance_b ILIKE :pattern_b)
       OR (substance_a ILIKE :pattern_b AND substance_b ILIKE :pattern_a)
    ORDER BY
        CASE niveau_contrainte
            WHEN 'Contre-indication' THEN 1
            WHEN 'Association déconseillée' THEN 2
            WHEN 'Précaution d''emploi' THEN 3
            ELSE 4
        END
    LIMIT 10
"""


def _sql_search(
    engine: object,
    pattern_a: str,
    pattern_b: str,
    seen: set[frozenset[str]],
) -> list[str]:
    """Run a pairwise SQL search and return formatted result lines."""
    from sqlalchemy import Engine

    assert isinstance(engine, Engine)
    lines: list[str] = []
    with engine.connect() as conn:
        rows = conn.execute(
            text(_SQL),
            {"pattern_a": f"%{pattern_a}%", "pattern_b": f"%{pattern_b}%"},
        ).fetchall()

    for row in rows:
        pair = frozenset([row[0], row[1]])
        if pair in seen:
            continue
        seen.add(pair)
        parts = [f"Interaction: {row[0]} + {row[1]}", f"Niveau de contrainte: {row[2]}"]
        if row[3]:
            parts.append(f"Nature du risque: {row[3]}")
        if row[4]:
            parts.append(f"Conduite à tenir: {row[4]}")
        lines.append(f"[{row[2]}] {row[0]} + {row[1]}\n{'. '.join(parts)}")

    return lines


def _discover_ansm_classes(collection: object, substance: str, top_n: int = 2) -> list[str]:
    """
    Use vector search to discover the ANSM pharmacological class name(s) for a substance.

    The ANSM thesaurus indexes interactions by class names (e.g. 'ANTIVITAMINES K'),
    not individual drug names. This function queries ChromaDB with the individual name
    and extracts the most frequently appearing class names from the top results.

    Example: 'warfarine' → ['ANTIVITAMINES K', 'ANTICOAGULANTS ORAUX']
    """
    import chromadb

    assert isinstance(collection, chromadb.Collection)
    results = collection.query(
        query_texts=[substance],
        n_results=10,
        include=["metadatas"],
    )
    metas = (results["metadatas"] or [[]])[0]

    counts: Counter[str] = Counter()
    for meta in metas:
        counts[str(meta["substance_a"])] += 1
        counts[str(meta["substance_b"])] += 1

    # Return the top_n most frequent names, excluding the query substance itself
    substance_upper = substance.upper()
    candidates = [
        name
        for name, _ in counts.most_common()
        if name.upper() != substance_upper
    ]
    return candidates[:top_n] if candidates else [substance]


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

    # Step 1: Direct SQL search (fast path — works when drug names appear in the thesaurus)
    sql_lines = _sql_search(engine, substance_a, substance_b, seen)

    # Step 2: Class discovery via ChromaDB + SQL retry
    # The ANSM thesaurus uses class names (e.g. 'ANTIVITAMINES K') not individual names.
    # We query ChromaDB to discover the likely class for each substance, then retry SQL.
    if not sql_lines:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        ef = get_embedding_function(settings.embedding_model)
        collection = client.get_collection(
            "idx_ansm_interaction_v1", embedding_function=ef  # type: ignore[arg-type]
        )

        classes_a = _discover_ansm_classes(collection, substance_a)
        classes_b = _discover_ansm_classes(collection, substance_b)

        for class_a in classes_a:
            for class_b in classes_b:
                if class_a == substance_a and class_b == substance_b:
                    continue  # already tried in step 1
                sql_lines += _sql_search(engine, class_a, class_b, seen)

    # Step 3: Vector search fallback — catches interactions missed by SQL
    if not sql_lines:
        if "client" not in dir():
            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            ef = get_embedding_function(settings.embedding_model)
            collection = client.get_collection(
                "idx_ansm_interaction_v1", embedding_function=ef  # type: ignore[arg-type]
            )

        query_terms = {substance_a.lower(), substance_b.lower()}

        def _substance_matches_query(substance: str) -> bool:
            s = substance.lower()
            return any(term in s or s in term for term in query_terms)

        vector_results = collection.query(
            query_texts=[f"{substance_a} {substance_b}"],
            n_results=5,
            include=["documents", "metadatas", "distances"],
        )
        docs = (vector_results["documents"] or [[]])[0]
        metas = (vector_results["metadatas"] or [[]])[0]
        distances = (vector_results["distances"] or [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            if not _substance_matches_query(
                str(meta["substance_a"])
            ) or not _substance_matches_query(str(meta["substance_b"])):
                continue
            sa, sb = str(meta["substance_a"]), str(meta["substance_b"])
            pair = frozenset([sa, sb])
            if pair not in seen:
                seen.add(pair)
                sql_lines.append(
                    f"[{meta['niveau_contrainte']}] {sa} + {sb}\n{doc}"  # noqa: E501
                )

    if not sql_lines:
        return (
            f"No interaction found between '{substance_a}' and '{substance_b}' "
            "in ANSM Thésaurus."
        )

    return "\n\n".join(sql_lines)
