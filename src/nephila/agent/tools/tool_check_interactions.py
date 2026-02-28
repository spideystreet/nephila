"""ANSM Thésaurus interaction lookup — dual SQL ILIKE + ChromaDB vector search."""

import logging
import re
import unicodedata

import chromadb
from langchain_core.tools import tool
from sqlalchemy import Engine, create_engine, text

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.embedder_local import get_embedding_function

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """Lowercase and strip accents for lexical matching."""
    nfkd = unicodedata.normalize("NFKD", name)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


def _resolve_ansm_names(substance: str, engine: "Engine") -> list[str]:
    """Resolve a substance DCI to its ANSM class names via the mapping table.

    Returns the list of matching classe_ansm values, or [substance] as fallback.
    """
    norm = _normalize(substance)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT classe_ansm FROM silver.silver_ansm__substance_class "
                    "WHERE substance_dci = :norm"
                ),
                {"norm": norm},
            ).fetchall()
        if rows:
            return [row[0] for row in rows]
    except Exception:
        logger.warning("Failed to resolve ANSM class for '%s'", substance, exc_info=True)
    return [substance]


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
    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)

    # Step 0: resolve substance DCI → ANSM class names
    names_a = _resolve_ansm_names(substance_a, engine)
    names_b = _resolve_ansm_names(substance_b, engine)

    # Step 1: SQL ILIKE — search all combinations of resolved names + originals
    all_names_a = list({substance_a, *names_a})
    all_names_b = list({substance_b, *names_b})

    seen: set[frozenset[str]] = set()
    sql_lines: list[str] = []

    # Build ILIKE conditions for all (a × b) name combinations
    # Use both original (accented) and normalized (unaccented) forms since
    # ILIKE is case-insensitive but accent-sensitive in PostgreSQL
    conditions: list[str] = []
    params: dict[str, str] = {}
    idx = 0
    for na in all_names_a:
        for nb in all_names_b:
            for va, vb in [(na, nb), (_normalize(na), _normalize(nb))]:
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
