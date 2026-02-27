"""Find generic equivalents for a drug by CIS code (SQL — Silver layer)."""

from langchain_core.tools import tool
from sqlalchemy import create_engine, text

from nephila.pipeline.config_pipeline import PipelineSettings

TYPE_LABELS = {"0": "Princeps", "1": "Générique", "2": "Générique par assimilation", "4": "CPP"}


@tool
def find_generics(cis: str) -> str:
    """
    Find generic equivalents for a drug identified by its CIS code (numeric string).
    Returns all drugs in the same BDPM generic group.
    type_generique: 0=princeps, 1=générique, 2=générique par assimilation, 4=CPP

    IMPORTANT: cis must be a numeric CIS code (e.g. '60001750'), not a drug name.
    Always call search_drug first to obtain the CIS code.
    """
    if not cis.strip().isdigit():
        return f"Error: '{cis}' is not a valid CIS code. Call search_drug first."

    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)

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
            {"cis": int(cis)},
        ).fetchall()

    if not rows:
        return f"No generic group found for CIS {cis}."

    lines = []
    for row in rows:
        label = TYPE_LABELS.get(str(row.type_generique), str(row.type_generique))
        lines.append(
            f"CIS {row.cis} [{label}]: {row.denomination} — {row.etat_commercialisation or 'N/A'}"
        )
    return "\n".join(lines)
