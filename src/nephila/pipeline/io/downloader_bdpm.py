"""
Download utilities for the Bronze layer.
Handles BDPM files (.txt, ISO-8859-1) and the ANSM Thésaurus (PDF).
"""
import re
from pathlib import Path

import httpx
from dagster import get_dagster_logger

# Files served at /download/file/{filename}
BDPM_FILES = [
    "CIS_bdpm.txt",
    "CIS_CIP_bdpm.txt",
    "CIS_COMPO_bdpm.txt",
    "CIS_GENER_bdpm.txt",
    "CIS_CPD_bdpm.txt",
]

# Files served at a different path (direct /download/{filename})
BDPM_FILES_DIRECT = [
    "CIS_InfoImportantes.txt",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Nephila/1.0; HealthTech Research)"
}


def download_file(url: str, dest: Path, timeout: int = 120) -> Path:
    log = get_dagster_logger()
    dest.parent.mkdir(parents=True, exist_ok=True)

    with httpx.stream("GET", url, headers=HEADERS, follow_redirects=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=8192):
                f.write(chunk)

    size_kb = dest.stat().st_size / 1024
    log.info(f"[bronze] {dest.name} — {size_kb:.1f} KB")
    return dest


def download_bdpm(base_url: str, dest_dir: Path) -> list[Path]:
    """Download all BDPM files into dest_dir/bdpm/.

    base_url should be the site root, e.g. https://base-donnees-publique.medicaments.gouv.fr
    """
    paths: list[Path] = []
    for filename in BDPM_FILES:
        url = f"{base_url}/download/file/{filename}"
        paths.append(download_file(url, dest_dir / "bdpm" / filename))
    for filename in BDPM_FILES_DIRECT:
        url = f"{base_url}/download/{filename}"
        paths.append(download_file(url, dest_dir / "bdpm" / filename))
    return paths


def find_ansm_pdf_url(page_url: str) -> str:
    """Scrape the ANSM page to extract the Thésaurus PDF download URL."""
    log = get_dagster_logger()

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        resp = client.get(page_url)
        resp.raise_for_status()

    # Look for PDF links containing "thesaurus" (case-insensitive)
    matches = re.findall(
        r'href=["\']([^"\']*thesaurus[^"\']*\.pdf)["\']',
        resp.text,
        re.IGNORECASE,
    )

    # Fallback: any PDF link on the page
    if not matches:
        matches = re.findall(r'href=["\']([^"\']+\.pdf)["\']', resp.text, re.IGNORECASE)

    if not matches:
        raise ValueError(f"No PDF found on ANSM page: {page_url}")

    pdf_url = matches[0]
    if not pdf_url.startswith("http"):
        pdf_url = "https://ansm.sante.fr" + pdf_url

    log.info(f"[bronze] ANSM Thésaurus found: {pdf_url}")
    return pdf_url
