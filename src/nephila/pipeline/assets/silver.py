"""
Silver layer — Données nettoyées et normalisées (PostgreSQL via dbt).
"""
from dagster import asset
from dagster_dbt import DbtCliResource


@asset(group_name="silver", deps=["bdpm_raw", "ansm_thesaurus_raw"])
def silver_bdpm(dbt: DbtCliResource) -> None:
    """Transformation dbt : bronze → silver (normalisation, FK CIS/CIP)."""
    dbt.cli(["run", "--select", "silver"]).wait()
