"""Bulk loader: reads Bronze .txt files and loads them into the PostgreSQL raw schema."""

from pathlib import Path
from typing import Any

import pandas as pd
from dagster import get_dagster_logger
from sqlalchemy import Engine, text

# Column definitions per BDPM source file (ISO-8859-1, tab-separated)
BDPM_FILE_COLUMNS: dict[str, list[str]] = {
    "CIS_bdpm.txt": [
        "cis",
        "denomination",
        "forme_pharma",
        "voies_admin",
        "statut_amm",
        "type_amm",
        "etat_commercialisation",
        "date_amm",
        "statut_bdm",
        "num_autorisation_eu",
        "titulaire",
        "surveillance_renforcee",
    ],
    "CIS_CIP_bdpm.txt": [
        "cis",
        "cip7",
        "libelle_presentation",
        "statut_admin",
        "etat_commercialisation",
        "date_declaration_commercialisation",
        "cip13",
        "agrement_collectivites",
        "taux_remboursement",
        "prix_medicament",
        "indicateurs_remboursement",
    ],
    "CIS_COMPO_bdpm.txt": [
        "cis",
        "designation_element",
        "code_substance",
        "denomination_substance",
        "dosage",
        "reference_dosage",
        "nature_composant",
        "num_liaison_sa_ft",
    ],
    "CIS_GENER_bdpm.txt": [
        "id_groupe",
        "libelle_groupe",
        "cis",
        "type_generique",
        "num_tri",
    ],
    "CIS_CPD_bdpm.txt": [
        "cis",
        "condition_prescription_delivrance",
    ],
    "CIS_InfoImportantes.txt": [
        "cis",
        "date_debut",
        "date_fin",
        "texte_info_importante",
    ],
}


def ensure_raw_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))


def load_bdpm_files_to_raw(bronze_dir: Path, engine: Engine) -> dict[str, int]:
    """
    Read all BDPM .txt files from bronze_dir and bulk-load them into the raw schema.
    Returns a dict of {table_name: row_count}.
    """
    log = get_dagster_logger()
    ensure_raw_schema(engine)
    results: dict[str, int] = {}

    for filename, columns in BDPM_FILE_COLUMNS.items():
        path = bronze_dir / "bdpm" / filename
        if not path.exists():
            raise FileNotFoundError(f"Bronze file not found: {path}")

        df = pd.read_csv(
            path,
            sep="\t",
            encoding="iso-8859-1",
            names=columns,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="warn",
        )
        # Replace empty strings with None for cleaner SQL NULLs
        df = df.replace("", None)

        table_name = filename.replace(".txt", "").lower()
        df.to_sql(
            table_name,
            engine,
            schema="raw",
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )
        results[table_name] = len(df)
        log.info(f"[raw] {table_name} — {len(df):,} rows loaded")

    return results


def load_interactions_to_raw(records: list[dict[str, Any]], engine: Engine) -> int:
    """Load parsed ANSM interaction records into raw.ansm_interaction."""
    log = get_dagster_logger()

    if not records:
        log.warning("[raw] No ANSM interaction records to load")
        return 0

    df = pd.DataFrame(records)
    df.to_sql(
        "ansm_interaction",
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )
    log.info(f"[raw] ansm_interaction — {len(df):,} rows loaded")
    return len(df)
