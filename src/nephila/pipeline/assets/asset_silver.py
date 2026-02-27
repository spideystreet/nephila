"""Silver layer — Load Bronze files into PostgreSQL raw schema, then run dbt transformations."""

from pathlib import Path

from dagster import AssetExecutionContext, AssetKey, AssetSpec, asset, multi_asset
from dagster_dbt import DbtCliResource, dbt_assets
from sqlalchemy import create_engine

from nephila.pipeline.config_pipeline import PipelineSettings
from nephila.pipeline.io.loader_bdpm import load_bdpm_files_to_raw, load_interactions_to_raw
from nephila.pipeline.io.loader_open_medic import load_open_medic_to_raw
from nephila.pipeline.io.parser_ansm import parse_thesaurus_pdf

DBT_MANIFEST = Path("dbt/target/manifest.json")

_BDPM_RAW_SPECS = [
    AssetSpec(AssetKey(["raw", "cis_bdpm"]), group_name="silver", deps=["bdpm_raw"]),
    AssetSpec(AssetKey(["raw", "cis_cip_bdpm"]), group_name="silver", deps=["bdpm_raw"]),
    AssetSpec(AssetKey(["raw", "cis_compo_bdpm"]), group_name="silver", deps=["bdpm_raw"]),
    AssetSpec(AssetKey(["raw", "cis_gener_bdpm"]), group_name="silver", deps=["bdpm_raw"]),
    AssetSpec(AssetKey(["raw", "cis_cpd_bdpm"]), group_name="silver", deps=["bdpm_raw"]),
    AssetSpec(AssetKey(["raw", "cis_infoimportantes"]), group_name="silver", deps=["bdpm_raw"]),
]


@multi_asset(specs=_BDPM_RAW_SPECS)
def bdpm_to_raw(context: AssetExecutionContext):  # type: ignore[no-untyped-def]
    """Load all BDPM .txt files from Bronze into the PostgreSQL raw schema."""
    settings = PipelineSettings()
    engine = create_engine(settings.postgres_dsn)
    results = load_bdpm_files_to_raw(settings.bronze_dir, engine)
    context.log.info(f"Loaded {len(results)} tables, {sum(results.values())} total rows")


@asset(
    key=AssetKey(["raw", "ansm_interaction"]),
    group_name="silver",
    deps=["ansm_thesaurus_raw"],
)
def ansm_to_raw(context: AssetExecutionContext) -> None:
    """Parse the ANSM Thésaurus PDF and load interaction records into raw.ansm_interaction."""
    settings = PipelineSettings()
    pdf_path = settings.bronze_dir / "ansm" / "thesaurus.pdf"
    records = parse_thesaurus_pdf(pdf_path)

    engine = create_engine(settings.postgres_dsn)
    count = load_interactions_to_raw(records, engine)
    context.add_output_metadata({"interactions_loaded": count})


@asset(
    key=AssetKey(["raw", "open_medic"]),
    group_name="silver",
    deps=["open_medic_raw"],
)
def open_medic_to_raw(context: AssetExecutionContext) -> None:
    """Load the Open Medic CIP13 CSV from Bronze into raw.open_medic."""
    settings = PipelineSettings()
    csv_path = (
        settings.bronze_dir / "open_medic" / f"NB_{settings.open_medic_year}_cip13.CSV.gz"
    )
    engine = create_engine(settings.postgres_dsn)
    count = load_open_medic_to_raw(csv_path, engine)
    context.add_output_metadata({"rows_loaded": count, "year": settings.open_medic_year})


@dbt_assets(manifest=DBT_MANIFEST, select="silver")
def silver_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource) -> None:  # type: ignore[misc]
    """Run and test dbt silver models. Each model becomes a Dagster asset; each dbt test becomes an asset check."""  # noqa: E501
    yield from dbt.cli(["build"], context=context).stream()
