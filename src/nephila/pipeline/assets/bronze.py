"""
Bronze layer — Raw ingestion des fichiers BDPM et du Thésaurus ANSM.
Encodage : ISO-8859-1, séparateur : tabulation.
"""
from dagster import asset


@asset(group_name="bronze")
def bdpm_raw() -> None:
    """Téléchargement et stockage brut des fichiers BDPM (.txt)."""
    ...


@asset(group_name="bronze")
def ansm_thesaurus_raw() -> None:
    """Téléchargement et parsing PDF du Thésaurus des interactions ANSM."""
    ...
