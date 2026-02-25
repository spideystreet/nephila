from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource

from nephila.pipeline.assets import asset_bronze, asset_silver, asset_gold

defs = Definitions(
    assets=load_assets_from_modules([asset_bronze, asset_silver, asset_gold]),
    resources={
        "dbt": DbtCliResource(project_dir="dbt", profiles_dir="dbt"),
    },
)
