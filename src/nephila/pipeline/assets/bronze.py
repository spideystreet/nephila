"""
Bronze layer — Raw ingestion of official data sources.
No transformation: files are stored as-is.
"""
from pathlib import Path

from dagster import AssetExecutionContext, asset

from nephila.pipeline.config import PipelineSettings
from nephila.pipeline.io.downloader import download_bdpm, download_file, find_ansm_pdf_url


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
