"""ANSM Thésaurus interaction lookup — dual SQL ILIKE + ChromaDB vector search."""
import chromadb
from langchain_core.tools import tool
from sqlalchemy import create_engine, text

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function


@tool
def check_interactions(substance: str) -> str:
    """
    Check ANSM Thésaurus for drug interactions involving a substance or drug class.

    The ANSM Thésaurus indexes interactions by drug CLASS names, not individual substance names.
    Examples: 'ANTIVITAMINES K' for warfarine/acenocoumarol, 'ANTIAGREGANTS PLAQUETTAIRES'
    for aspirin, 'INHIBITEURS DE LA MAO' for MAOIs, 'FLUOROQUINOLONES' for ciprofloxacin.
    Always try the ANSM pharmacological class name when known — it yields exact matches.

    Returns interactions with their constraint level.
    ALWAYS call this before any drug recommendation.
    Constraint levels: Contre-indication > Association déconseillée > Précaution d'emploi > A prendre en compte
    """
    settings = PipelineSettings()

    # Step 1: SQL ILIKE — exact/partial match on ANSM substance group names
    engine = create_engine(settings.postgres_dsn)
    seen: set[str] = set()
    sql_lines: list[str] = []

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT substance_a, substance_b, niveau_contrainte, nature_risque, conduite_a_tenir
                FROM silver.silver_ansm__interaction
                WHERE substance_a ILIKE :pattern OR substance_b ILIKE :pattern
                ORDER BY
                    CASE niveau_contrainte
                        WHEN 'Contre-indication' THEN 1
                        WHEN 'Association déconseillée' THEN 2
                        WHEN 'Précaution d''emploi' THEN 3
                        ELSE 4
                    END
                LIMIT 20
            """),
            {"pattern": f"%{substance}%"},
        ).fetchall()

    for row in rows:
        key = f"{row[0]}|{row[1]}"
        if key not in seen:
            seen.add(key)
            parts = [
                f"Interaction: {row[0]} + {row[1]}",
                f"Niveau de contrainte: {row[2]}",
            ]
            if row[3]:
                parts.append(f"Nature du risque: {row[3]}")
            if row[4]:
                parts.append(f"Conduite à tenir: {row[4]}")
            sql_lines.append(f"[{row[2]}] {row[0]} + {row[1]}\n{'. '.join(parts)}")

    # Step 2: vector search — semantic fallback for class names the LLM didn't resolve
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    ef = get_embedding_function(settings.embedding_model)
    collection = client.get_collection("idx_ansm_interaction_v1", embedding_function=ef)

    vector_results = collection.query(
        query_texts=[substance],
        n_results=10,
        include=["documents", "metadatas"],
    )

    vector_lines: list[str] = []
    for doc, meta in zip(vector_results["documents"][0], vector_results["metadatas"][0]):
        key = f"{meta['substance_a']}|{meta['substance_b']}"
        if key not in seen:
            seen.add(key)
            vector_lines.append(
                f"[{meta['niveau_contrainte']}] {meta['substance_a']} + {meta['substance_b']}\n{doc}"
            )

    all_results = sql_lines + vector_lines
    if not all_results:
        return f"No interactions found for '{substance}' in ANSM Thésaurus."

    return "\n\n".join(all_results)
