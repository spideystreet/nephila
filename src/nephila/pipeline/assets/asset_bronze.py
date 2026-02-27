"""
Bronze layer — Raw ingestion of official data sources.
No transformation: files are stored as-is.
"""

from pathlib import Path

from dagster import AssetExecutionContext, asset

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.downloader_bdpm import download_bdpm, download_file, find_ansm_pdf_url
from nephila.pipeline.io.downloader_open_medic import download_open_medic_cip13


@asset(group_name="bronze")
def bdpm_raw(context: AssetExecutionContext) -> None:
    """
    Download BDPM files from base-donnees-publique.medicaments.gouv.fr.
    Source encoding: ISO-8859-1, separator: tab.
    Output: data/bronze/bdpm/
    """
    settings = PipelineSettings()
    files = download_bdpm(settings.bdpm_base_url, settings.bronze_dir)

    context.add_output_metadata(
        {
            "files": [f.name for f in files],
            "count": len(files),
            "dest_dir": str(settings.bronze_dir / "bdpm"),
        }
    )


@asset(group_name="bronze")
def ansm_thesaurus_raw(context: AssetExecutionContext) -> None:
    """
    Download the ANSM drug interaction Thésaurus PDF.
    The PDF URL is scraped from the official ANSM page (changes with each release).
    Output: data/bronze/ansm/thesaurus.pdf
    """
    settings = PipelineSettings()
    dest: Path = settings.bronze_dir / "ansm" / "thesaurus.pdf"

    pdf_url = find_ansm_pdf_url(settings.ansm_thesaurus_page_url)
    path = download_file(pdf_url, dest)

    context.add_output_metadata(
        {
            "source_url": pdf_url,
            "dest": str(path),
            "size_kb": round(path.stat().st_size / 1024, 1),
        }
    )


@asset(group_name="bronze")
def open_medic_raw(context: AssetExecutionContext) -> None:
    """
    Download the Open Medic CIP13 annual CSV from ameli.fr (CNAM).
    Data: drug reimbursements aggregated by CIP13 code with ATC classification.
    Output: data/bronze/open_medic/open_medic_cip13_{year}.csv
    """
    settings = PipelineSettings()
    path = download_open_medic_cip13(
        settings.open_medic_base_url,
        settings.open_medic_year,
        settings.bronze_dir,
    )

    context.add_output_metadata(
        {
            "year": settings.open_medic_year,
            "dest": str(path),
            "size_kb": round(path.stat().st_size / 1024, 1),
        }
    )
