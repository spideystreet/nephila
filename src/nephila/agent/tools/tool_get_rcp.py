"""Fetch RCP (Résumé des Caractéristiques du Produit) links from Silver layer."""
from langchain_core.tools import tool
from sqlalchemy import create_engine, text

from nephila.pipeline.config_pipeline import PipelineSettings


@tool
def get_rcp(cis: str) -> str:
    """
    Get the RCP (Résumé des Caractéristiques du Produit) and important safety info for a drug.
    Always cite this in responses. Never give medical advice without referencing the RCP.
    """
    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT texte_info_importante, date_debut, date_fin
                FROM silver.silver_bdpm__info_importante
                WHERE cis = :cis
                ORDER BY date_debut DESC NULLS LAST
            """),
            {"cis": int(cis)},
        ).fetchall()

    if not rows:
        return f"No RCP information found for CIS {cis}. Refer to base-donnees-publique.medicaments.gouv.fr"

    lines = [f"RCP / Important information for CIS {cis}:"]
    for row in rows:
        date = f"(from {row.date_debut})" if row.date_debut else ""
        lines.append(f"  {date} {row.texte_info_importante or '(see BDPM for RCP link)'}")
    return "\n".join(lines)
