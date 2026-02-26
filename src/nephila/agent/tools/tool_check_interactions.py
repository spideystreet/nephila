"""ANSM Thésaurus interaction lookup — dual SQL ILIKE + ChromaDB vector search."""

import chromadb
from langchain_core.tools import tool
from sqlalchemy import create_engine, text

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function


@tool
def check_interactions(substance_a: str, substance_b: str) -> str:
    """
    Check ANSM Thésaurus for the interaction between two substances or drug classes.

    The ANSM Thésaurus indexes interactions by drug CLASS names, not individual substance names.
    Examples: 'ANTIVITAMINES K' for warfarine/acenocoumarol, 'ANTIAGREGANTS PLAQUETTAIRES'
    for aspirin, 'INHIBITEURS DE LA MAO' for MAOIs, 'FLUOROQUINOLONES' for ciprofloxacin,
    'ANTIFONGIQUES AZOLÉS' for fluconazole/itraconazole, 'STATINES' for statins,
    'INHIBITEURS DE RECAPTURE DE LA SEROTONINE' for SSRIs.
    Always use the ANSM pharmacological class name when known — it yields exact matches.
    When the class is unknown, pass the individual substance name as fallback.

    Returns the interaction between substance_a and substance_b with its constraint level.
    ALWAYS call this before any drug recommendation.
    Constraint levels: Contre-indication > Association déconseillée
    > Précaution d'emploi > A prendre en compte
    """
    settings = PipelineSettings()

    # Step 1: SQL ILIKE — search for the specific interaction between the two substances
    engine = create_engine(settings.postgres_dsn)
    seen: set[frozenset[str]] = set()
    sql_lines: list[str] = []

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
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
            """),
            {"pattern_a": f"%{substance_a}%", "pattern_b": f"%{substance_b}%"},
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
    collection = client.get_collection("idx_ansm_interaction_v1", embedding_function=ef)  # type: ignore[arg-type]

    vector_results = collection.query(
        query_texts=[f"{substance_a} {substance_b}"],
        n_results=3,
        include=["documents", "metadatas"],
    )

    vector_lines: list[str] = []
    docs = (vector_results["documents"] or [[]])[0]
    metas = (vector_results["metadatas"] or [[]])[0]
    for doc, meta in zip(docs, metas):
        pair = frozenset([meta["substance_a"], meta["substance_b"]])
        if pair not in seen:
            seen.add(pair)
            vector_lines.append(
                f"[{meta['niveau_contrainte']}] {meta['substance_a']} + {meta['substance_b']}\n{doc}"  # noqa: E501
            )

    all_results = sql_lines + vector_lines
    if not all_results:
        return (
            f"No interaction found between '{substance_a}' and '{substance_b}' in ANSM Thésaurus. "
            "Try using the ANSM pharmacological class names (e.g. 'ANTIVITAMINES K', 'STATINES')."
        )

    return "\n\n".join(all_results)
