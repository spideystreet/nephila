"""Typed SQL queries for agent tools — returns validated Pydantic models."""

import logging
import threading
import unicodedata

from sqlalchemy import Engine, create_engine, text

from nephila.models.model_ansm import InteractionRow
from nephila.models.model_queries import GeneriqueResult, RcpRow
from nephila.pipeline.config_pipeline import PipelineSettings

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_engine_lock = threading.Lock()


def _get_engine() -> Engine:
    """Return a lazily-created singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                settings = PipelineSettings()
                _engine = create_engine(settings.postgres_dsn)
    return _engine


def _normalize(name: str) -> str:
    """Lowercase and strip accents for lexical matching."""
    nfkd = unicodedata.normalize("NFKD", name)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


def resolve_ansm_classes(substance: str) -> list[str]:
    """Resolve a substance DCI to its ANSM class names via the mapping table.

    Returns the list of matching classe_ansm values, or [substance] as fallback.
    """
    engine = _get_engine()
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


def find_interactions(substance_a: str, substance_b: str) -> list[InteractionRow]:
    """Find ANSM interactions between two substances using ILIKE search.

    Resolves substance names internally and searches all combinations
    of original + normalized forms to handle accent mismatches.
    """
    engine = _get_engine()

    names_a = resolve_ansm_classes(substance_a)
    names_b = resolve_ansm_classes(substance_b)

    all_names_a = list({substance_a, *names_a})
    all_names_b = list({substance_b, *names_b})

    conditions: list[str] = []
    params: dict[str, str] = {}
    idx = 0
    for na in all_names_a:
        for nb in all_names_b:
            na_norm, nb_norm = _normalize(na), _normalize(nb)
            for va, vb in [(na, nb), (na_norm, nb_norm), (na_norm, nb), (na, nb_norm)]:
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

    return [
        InteractionRow(
            substance_a=row[0],
            substance_b=row[1],
            niveau_contrainte=row[2],
            nature_risque=row[3],
            conduite_a_tenir=row[4],
        )
        for row in rows
    ]


def find_generics_by_cis(cis: int) -> list[GeneriqueResult]:
    """Find all drugs in the same BDPM generic group as the given CIS code."""
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT m.cis, m.denomination, g.type_generique, m.etat_commercialisation
                FROM silver.silver_bdpm__generique g
                JOIN silver.silver_bdpm__medicament m ON g.cis = m.cis
                WHERE g.id_groupe = (
                    SELECT id_groupe FROM silver.silver_bdpm__generique
                    WHERE cis = :cis LIMIT 1
                )
                ORDER BY g.type_generique, m.denomination
            """),
            {"cis": cis},
        ).fetchall()

    return [
        GeneriqueResult(
            cis=row[0],
            denomination=row[1],
            type_generique=str(row[2]),
            etat_commercialisation=row[3],
        )
        for row in rows
    ]


def get_rcp_info(cis: int) -> list[RcpRow]:
    """Fetch RCP important safety information for a drug by CIS code."""
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT texte_info_importante, date_debut, date_fin
                FROM silver.silver_bdpm__info_importante
                WHERE cis = :cis
                ORDER BY date_debut DESC NULLS LAST
            """),
            {"cis": cis},
        ).fetchall()

    return [
        RcpRow(
            texte_info_importante=row[0],
            date_debut=row[1],
            date_fin=row[2],
        )
        for row in rows
    ]
