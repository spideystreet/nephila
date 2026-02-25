"""Silver layer — Load Bronze files into PostgreSQL raw schema, then run dbt transformations."""
from dagster import AssetExecutionContext, asset
from dagster_dbt import DbtCliResource
from sqlalchemy import create_engine

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.parser_ansm import parse_thesaurus_pdf
from nephila.pipeline.io.loader_bdpm import load_bdpm_files_to_raw, load_interactions_to_raw


@asset(group_name="silver", deps=["bdpm_raw"])
def bdpm_to_raw(context: AssetExecutionContext) -> None:
    """Load all BDPM .txt files from Bronze into the PostgreSQL raw schema."""
    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)
    results = load_bdpm_files_to_raw(settings.bronze_dir, engine)
    context.add_output_metadata(
        {"tables": list(results.keys()), "total_rows": sum(results.values())}
    )


@asset(group_name="silver", deps=["ansm_thesaurus_raw"])
def ansm_to_raw(context: AssetExecutionContext) -> None:
    """Parse the ANSM Thésaurus PDF and load interaction records into raw.ansm_interaction."""
    settings = PipelineSettings()
    pdf_path = settings.bronze_dir / "ansm" / "thesaurus.pdf"
    records = parse_thesaurus_pdf(pdf_path)

    engine = create_engine(settings.postgres_dsn)
    count = load_interactions_to_raw(records, engine)
    context.add_output_metadata({"interactions_loaded": count})


@asset(group_name="silver", deps=["bdpm_to_raw", "ansm_to_raw"])
def silver_dbt(context: AssetExecutionContext, dbt: DbtCliResource) -> None:
    """Run dbt models to transform raw schema into normalized Silver tables."""
    dbt.cli(["run", "--select", "silver"]).wait()
