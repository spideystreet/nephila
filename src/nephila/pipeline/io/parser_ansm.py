"""
ANSM Thésaurus PDF parser.
Extracts drug interaction records from the official ANSM PDF publication.
The PDF structure varies across releases; this parser uses heuristics on table headers.
"""
from pathlib import Path

import pdfplumber
from dagster import get_dagster_logger

# Known column header keywords for each field
_SUBSTANCE_B_KEYWORDS = ("substances", "médicaments", "medicaments", "classes")
_CONSTRAINT_KEYWORDS = ("niveau", "contrainte")
_RISK_KEYWORDS = ("risque", "nature", "mécanisme", "mecanisme")
_CONDUCT_KEYWORDS = ("conduite", "tenir")

# Recognized constraint level prefixes (for row-level filtering)
VALID_CONSTRAINT_LEVELS = (
    "contre-indication",
    "association déconseillée",
    "précaution d'emploi",
    "à prendre en compte",
    "a prendre en compte",
)


def _map_columns(header: list[str]) -> dict[str, int] | None:
    """Map column header cells to field names. Returns None if table is not an interaction table."""
    col_map: dict[str, int] = {}
    for i, cell in enumerate(header):
        cell_lower = cell.lower().strip()
        if any(kw in cell_lower for kw in _SUBSTANCE_B_KEYWORDS):
            col_map["substance_b"] = i
        elif any(kw in cell_lower for kw in _CONSTRAINT_KEYWORDS):
            col_map["niveau_contrainte"] = i
        elif any(kw in cell_lower for kw in _RISK_KEYWORDS):
            col_map["nature_risque"] = i
        elif any(kw in cell_lower for kw in _CONDUCT_KEYWORDS):
            col_map["conduite_a_tenir"] = i

    # An interaction table must have at least these two columns
    if "substance_b" not in col_map or "niveau_contrainte" not in col_map:
        return None
    return col_map


def _extract_row(row: list, col_map: dict[str, int], substance_a: str) -> dict | None:
    """Extract a single interaction record from a table row."""

    def cell(key: str) -> str | None:
        idx = col_map.get(key)
        if idx is None or idx >= len(row):
            return None
        val = row[idx]
        return str(val).strip() if val else None

    substance_b = cell("substance_b")
    niveau = cell("niveau_contrainte")

    if not substance_b or not niveau:
        return None

    # Filter rows that don't look like real interaction entries
    niveau_lower = niveau.lower()
    if not any(niveau_lower.startswith(lvl) for lvl in VALID_CONSTRAINT_LEVELS):
        return None

    return {
        "substance_a": substance_a,
        "substance_b": substance_b,
        "niveau_contrainte": niveau,
        "nature_risque": cell("nature_risque"),
        "conduite_a_tenir": cell("conduite_a_tenir"),
    }


def parse_thesaurus_pdf(pdf_path: Path) -> list[dict]:
    """
    Parse the ANSM Thésaurus PDF and return a list of interaction records.
    Each record contains: substance_a, substance_b, niveau_contrainte,
    nature_risque, conduite_a_tenir.
    """
    log = get_dagster_logger()
    records: list[dict] = []
    current_substance: str = "UNKNOWN"
    pages_processed = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Attempt to extract the substance name from page text (appears as section header)
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                # Substance headers are typically short uppercase lines
                if line.isupper() and 3 < len(line) < 80:
                    current_substance = line
                    break

            tables = page.extract_tables(
                {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
            )
            for table in tables:
                if not table or len(table) < 2:
                    continue

                header = [str(c).strip() if c else "" for c in table[0]]
                col_map = _map_columns(header)
                if col_map is None:
                    continue

                for row in table[1:]:
                    record = _extract_row(row, col_map, current_substance)
                    if record:
                        records.append(record)

            pages_processed += 1

    log.info(
        f"[bronze] ANSM parser — {pages_processed} pages, {len(records)} interactions extracted"
    )
    return records
