"""Download utilities for Open Medic (CNAM Assurance Maladie) data."""

import re
from pathlib import Path

from dagster import get_dagster_logger

from nephila.pipeline.io.downloader_bdpm import HEADERS, download_file


def download_open_medic_cip13(base_url: str, year: int, dest_dir: Path) -> Path:
    """
    Download the Open Medic CIP13 aggregate CSV.gz from ameli.fr.

    The CNAM server uses a two-step mechanism:
    1. GET {base_url}/download2.php?Dir_Rep={year}_CIP13
       → returns HTML listing with tokenised download links
    2. Parse the HTML to find NB_{year}_cip13.CSV.gz and extract its URL
    3. Download the file

    Output: dest_dir/open_medic/NB_{year}_cip13.CSV.gz
    """
    import httpx

    log = get_dagster_logger()

    listing_url = f"{base_url}/download2.php?Dir_Rep={year}_CIP13"
    log.info(f"[bronze] Fetching Open Medic file listing: {listing_url}")

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        resp = client.get(listing_url)
        resp.raise_for_status()

    # Find the link to the aggregate CIP13 file (no demographic breakdown)
    target_filename = f"NB_{year}_cip13.CSV.gz"
    pattern = rf'href="([^"]*{re.escape(target_filename)}[^"]*)"'
    matches = re.findall(pattern, resp.text, re.IGNORECASE)

    if not matches:
        all_links = re.findall(r'href="([^"]+)"', resp.text)
        raise ValueError(
            f"Could not find {target_filename} in Open Medic listing. Available links: {all_links}"
        )

    relative_url = matches[0]
    if relative_url.startswith("./"):
        download_url = f"{base_url}/{relative_url[2:]}"
    elif relative_url.startswith("/"):
        download_url = f"https://open-data-assurance-maladie.ameli.fr{relative_url}"
    else:
        download_url = relative_url

    log.info(f"[bronze] Open Medic CIP13 download URL: {download_url}")

    dest = dest_dir / "open_medic" / target_filename
    return download_file(download_url, dest)
