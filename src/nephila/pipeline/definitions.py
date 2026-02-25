from dagster import Definitions, load_assets_from_modules

from nephila.pipeline.assets import bronze, silver, gold

defs = Definitions(
    assets=load_assets_from_modules([bronze, silver, gold]),
)
