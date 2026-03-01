"""Find generic equivalents for a drug by CIS code (SQL — Silver layer)."""

from langchain_core.tools import tool

from nephila.agent.queries import find_generics_by_cis

TYPE_LABELS = {"0": "Princeps", "1": "Générique", "2": "Générique par assimilation", "4": "CPP"}


@tool
def find_generics(cis: str) -> str:
    """
    Find generic equivalents for a drug identified by its CIS code.
    Returns all drugs in the same BDPM generic group.
    type_generique: 0=princeps, 1=générique, 2=générique par assimilation, 4=CPP
    """
    cis = cis.strip()
    if not cis.isdigit():
        return f"Invalid CIS code '{cis}'. Use search_drug to find the CIS code first."

    rows = find_generics_by_cis(int(cis))

    if not rows:
        return f"No generic group found for CIS {cis}."

    lines = []
    for row in rows:
        label = TYPE_LABELS.get(row.type_generique, row.type_generique)
        lines.append(
            f"CIS {row.cis} [{label}]: {row.denomination} — {row.etat_commercialisation or 'N/A'}"
        )
    return "\n".join(lines)
