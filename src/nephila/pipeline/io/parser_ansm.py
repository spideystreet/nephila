"""
ANSM Thésaurus PDF parser.
Extracts drug interaction records from the official ANSM PDF publication.
The PDF uses a text-column layout (not structured tables): interactions are
parsed from raw page text using line-by-line heuristics.
"""

import re
from pathlib import Path
from typing import Any

import pdfplumber
from dagster import get_dagster_logger

# Constraint level aliases — map normalized forms to canonical labels
_CONSTRAINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bcontre[-\s]indication\b", re.IGNORECASE), "Contre-indication"),
    (re.compile(r"\bCI\b"), "Contre-indication"),
    (
        re.compile(r"\bassociation\s+d[ée]conseill[ée]e\b", re.IGNORECASE),
        "Association déconseillée",
    ),  # noqa: E501
    (re.compile(r"\bASDEC\b"), "Association déconseillée"),
    (re.compile(r"\bpr[ée]caution\s+d.emploi\b", re.IGNORECASE), "Précaution d'emploi"),
    (re.compile(r"\bPE\b"), "Précaution d'emploi"),
    (re.compile(r"\b[àa]\s+prendre\s+en\s+compte\b", re.IGNORECASE), "A prendre en compte"),
    (re.compile(r"\bAPEC\b"), "A prendre en compte"),
]

_SUBSTANCE_A_RE = re.compile(r"^[A-ZÀÁÂÄÇÉÈÊËÎÏÔÙÛÜ\s,\'\-/\(\)\.0-9]{3,80}$")


def _detect_constraint(text: str) -> str | None:
    """Return the highest-priority constraint level found in text, or None."""
    # Priority order: CI > ASDEC > PE > APEC
    for pattern, label in _CONSTRAINT_PATTERNS:
        if pattern.search(text):
            return label
    return None


def _is_substance_a(line: str) -> bool:
    """True if the line looks like a substance A header (all-caps, not starting with +)."""
    if line.startswith("+") or line.startswith("Voir") or line.startswith("voir"):
        return False
    # Exclude page numbers (purely numeric lines like "2", "100", "183")
    if line.strip().isdigit():
        return False
    # Require at least 2 uppercase letters — excludes section artifacts like "165." or "I."
    if sum(1 for c in line if c.isupper()) < 2:
        return False
    return bool(_SUBSTANCE_A_RE.match(line))


def parse_thesaurus_pdf(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Parse the ANSM Thésaurus PDF and return a list of interaction records.
    Each record contains: substance_a, substance_b, niveau_contrainte,
    nature_risque, conduite_a_tenir (always None — not extractable from this layout).
    """
    log = get_dagster_logger()
    records: list[dict[str, Any]] = []
    current_substance_a: str = "UNKNOWN"
    current_substance_b: str | None = None
    description_lines: list[str] = []
    pages_processed = 0

    def flush_interaction() -> None:
        """Emit current substance_b + accumulated description as a record."""
        if not current_substance_b:
            return
        description = " ".join(description_lines)
        niveau = _detect_constraint(description)
        if niveau:
            # Strip the constraint level tokens from the nature_risque text
            nature = description
            for pattern, _ in _CONSTRAINT_PATTERNS:
                nature = pattern.sub("", nature).strip(" -–•")
            records.append(
                {
                    "substance_a": current_substance_a,
                    "substance_b": current_substance_b,
                    "niveau_contrainte": niveau,
                    "nature_risque": nature or None,
                    "conduite_a_tenir": None,
                }
            )

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                if line.startswith("+"):
                    # New substance B → flush previous interaction first
                    flush_interaction()
                    current_substance_b = line.lstrip("+").strip()
                    description_lines = []

                elif _is_substance_a(line):
                    # New substance A section → flush previous interaction
                    flush_interaction()
                    current_substance_b = None
                    description_lines = []
                    current_substance_a = line

                elif current_substance_b is not None:
                    # Accumulate description / risk / constraint text
                    description_lines.append(line)

            # Flush at end of page (interaction may span pages — keep state)
            pages_processed += 1

    # Final flush
    flush_interaction()

    log.info(
        f"[bronze] ANSM parser — {pages_processed} pages, {len(records)} interactions extracted"
    )
    return records
