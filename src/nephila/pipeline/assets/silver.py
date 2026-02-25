"""
Silver layer — Cleaned and normalized data (PostgreSQL via dbt).
"""
from dagster import asset
from dagster_dbt import DbtCliResource


@asset(group_name="silver", deps=["bdpm_raw", "ansm_thesaurus_raw"])
def silver_bdpm(dbt: DbtCliResource) -> None:
    """Run dbt models to normalize Bronze data into Silver (CIS/CIP FK constraints)."""
    dbt.cli(["run", "--select", "silver"]).wait()
