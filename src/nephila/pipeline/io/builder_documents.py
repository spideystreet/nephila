"""
Build ChromaDB documents (text + metadata) from Silver PostgreSQL tables.
One document per CIS for medicaments, one per interaction row for ANSM.
"""

import hashlib

import pandas as pd
from sqlalchemy import Engine


def build_medicament_documents(
    engine: Engine,
) -> tuple[list[str], list[str], list[dict]]:
    """
    Join silver_bdpm__medicament + silver_bdpm__composition into one document per CIS.
    Returns (ids, documents, metadatas).
    """
    df = pd.read_sql(
        """
        SELECT
            m.cis::TEXT                      AS cis,
            m.denomination,
            m.forme_pharma,
            m.voies_admin,
            m.etat_commercialisation,
            m.titulaire,
            STRING_AGG(
                c.denomination_substance ||
                CASE WHEN c.dosage IS NOT NULL THEN ' ' || c.dosage ELSE '' END,
                '; ' ORDER BY c.denomination_substance
            ) AS substances
        FROM silver.silver_bdpm__medicament m
        LEFT JOIN silver.silver_bdpm__composition c
            ON m.cis = c.cis AND c.nature_composant = 'SA'
        GROUP BY m.cis, m.denomination, m.forme_pharma, m.voies_admin,
                 m.etat_commercialisation, m.titulaire
        """,
        engine,
    )

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for row in df.itertuples():
        ids.append(str(row.cis))
        documents.append(_format_medicament(row))
        metadatas.append(
            {
                "cis": int(row.cis),
                "etat_commercialisation": row.etat_commercialisation or "",
            }
        )

    return ids, documents, metadatas


def build_interaction_documents(
    engine: Engine,
) -> tuple[list[str], list[str], list[dict]]:
    """
    Build one document per ANSM interaction row.
    Returns (ids, documents, metadatas).
    """
    df = pd.read_sql("SELECT * FROM silver.silver_ansm__interaction", engine)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for row in df.itertuples():
        key = f"{row.substance_a}|{row.substance_b}"
        ids.append(hashlib.md5(key.encode()).hexdigest())
        documents.append(_format_interaction(row))
        metadatas.append(
            {
                "substance_a": row.substance_a,
                "substance_b": row.substance_b,
                "niveau_contrainte": row.niveau_contrainte,
            }
        )

    return ids, documents, metadatas


def _format_medicament(row) -> str:  # type: ignore[no-untyped-def]
    parts = [f"{row.denomination} ({row.forme_pharma}, {row.voies_admin})"]
    if row.substances:
        parts.append(f"Substances actives: {row.substances}")
    if row.etat_commercialisation:
        parts.append(f"Statut: {row.etat_commercialisation}")
    if row.titulaire:
        parts.append(f"Titulaire: {row.titulaire}")
    return ". ".join(parts)


def _format_interaction(row) -> str:  # type: ignore[no-untyped-def]
    parts = [
        f"Interaction: {row.substance_a} + {row.substance_b}",
        f"Niveau de contrainte: {row.niveau_contrainte}",
    ]
    if row.nature_risque:
        parts.append(f"Nature du risque: {row.nature_risque}")
    if row.conduite_a_tenir:
        parts.append(f"Conduite à tenir: {row.conduite_a_tenir}")
    return ". ".join(parts)
