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

    Requires count >= 2 to suppress single-occurrence noise (unrelated classes that
    happen to appear once when the substance is unknown to the thesaurus).

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

    # Count only from substance_a: in the ANSM thesaurus, the pharmacological class for
    # a substance consistently appears as substance_a across many interactions.
    # Counting substance_b would pick up interaction partners (e.g. METHOTREXATE when
    # querying "ibuprofène") and incorrectly treat them as classes for our substance.
    counts: Counter[str] = Counter()
    for meta in metas:
        counts[str(meta["substance_a"])] += 1

    substance_upper = substance.upper()
    candidates = [
        name
        for name, count in counts.most_common()
        if name.upper() != substance_upper and count >= 2
    ]
    return candidates[:top_n] if candidates else []


def _find_partner_classes(
    collection: object,
    class_a: str,
    substance_b: str,
    top_n: int = 3,
) -> list[str]:
    """
    Given a known ANSM class name for substance A, find the ANSM class name(s) for
    substance B by querying ChromaDB with the combined '{class_a} {substance_b}' text.

    This resolves the synonym gap: e.g. 'ANTICOAGULANTS ORAUX aspirine' → returns
    'ACIDE ACETYLSALICYLIQUE' as the thesaurus name for 'aspirine'.
    """
    import chromadb

    assert isinstance(collection, chromadb.Collection)
    results = collection.query(
        query_texts=[f"{class_a} {substance_b}"],
        n_results=5,
        include=["metadatas"],
    )
    metas = (results["metadatas"] or [[]])[0]

    class_a_upper = class_a.upper()
    seen: set[str] = set()
    candidates: list[str] = []
    for meta in metas:
        for key in ("substance_a", "substance_b"):
            name = str(meta[key])
            if name.upper() != class_a_upper and name not in seen:
                seen.add(name)
                candidates.append(name)
    return candidates[:top_n]


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

    # Step 2: Guided class discovery via ChromaDB + SQL retry.
    # Strategy: discover the ANSM class for substance_a (e.g. 'warfarine' → 'ANTICOAGULANTS ORAUX'),
    # then for each discovered class query ChromaDB with "{class_a} {substance_b}" to find the
    # ANSM class for substance_b (e.g. 'ANTICOAGULANTS ORAUX aspirine' → 'ACIDE ACETYLSALICYLIQUE').
    # This resolves synonym gaps that neither direct SQL nor individual class discovery can bridge.
    if not sql_lines:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        ef = get_embedding_function(settings.embedding_model)
        collection = client.get_collection(
            "idx_ansm_interaction_v1", embedding_function=ef  # type: ignore[arg-type]
        )

        classes_a = _discover_ansm_classes(collection, substance_a)
        for class_a in classes_a:
            partner_classes = _find_partner_classes(collection, class_a, substance_b)
            for class_b in partner_classes:
                sql_lines += _sql_search(engine, class_a, class_b, seen)

        # Symmetric pass: discover classes for substance_b, find partners for substance_a
        if not sql_lines:
            classes_b = _discover_ansm_classes(collection, substance_b)
            for class_b in classes_b:
                partner_classes = _find_partner_classes(collection, class_b, substance_a)
                for class_a in partner_classes:
                    sql_lines += _sql_search(engine, class_a, class_b, seen)

    # Step 3: Vector search fallback — catches interactions missed by SQL
    if not sql_lines:
        if "client" not in dir():
            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            ef = get_embedding_function(settings.embedding_model)
            collection = client.get_collection(
                "idx_ansm_interaction_v1", embedding_function=ef  # type: ignore[arg-type]
            )

        # Last resort: take the single most semantically similar result.
        # We reach this only if both SQL and guided class discovery failed.
        # Limiting to 1 result minimises false positives; the embedding similarity
        # for the combined "{substance_a} {substance_b}" query is our best proxy.
        vector_results = collection.query(
            query_texts=[f"{substance_a} {substance_b}"],
            n_results=1,
            include=["documents", "metadatas"],
        )
        docs = (vector_results["documents"] or [[]])[0]
        metas = (vector_results["metadatas"] or [[]])[0]

        for doc, meta in zip(docs, metas):
            sa, sb = str(meta["substance_a"]), str(meta["substance_b"])
            pair = frozenset([sa, sb])
            if pair not in seen:
                seen.add(pair)
                sql_lines.append(f"[{meta['niveau_contrainte']}] {sa} + {sb}\n{doc}")

    if not sql_lines:
        return (
            f"No interaction found between '{substance_a}' and '{substance_b}' "
            "in ANSM Thésaurus."
        )

    return "\n\n".join(sql_lines)
