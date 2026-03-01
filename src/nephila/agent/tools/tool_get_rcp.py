"""Fetch RCP (Résumé des Caractéristiques du Produit) links from Silver layer."""

from langchain_core.tools import tool

from nephila.agent.queries import get_rcp_info


@tool
def get_rcp(cis: str) -> str:
    """
    Get the RCP (Résumé des Caractéristiques du Produit) and important safety info for a drug.
    Always cite this in responses. Never give medical advice without referencing the RCP.
    """
    cis = cis.strip()
    if not cis.isdigit():
        return f"Invalid CIS code '{cis}'. Use search_drug to find the CIS code first."

    rows = get_rcp_info(int(cis))

    if not rows:
        return f"No RCP information found for CIS {cis}. Refer to base-donnees-publique.medicaments.gouv.fr"  # noqa: E501

    lines = [f"RCP / Important information for CIS {cis}:"]
    for row in rows:
        date = f"(from {row.date_debut})" if row.date_debut else ""
        lines.append(f"  {date} {row.texte_info_importante or '(see BDPM for RCP link)'}")
    return "\n".join(lines)
