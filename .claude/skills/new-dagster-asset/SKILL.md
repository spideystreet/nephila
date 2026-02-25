# Skill: Add a New Dagster Asset

## Steps

1. **Choose the layer file**: `asset_bronze.py`, `asset_silver.py`, or `asset_gold.py`.

2. **Declare the asset**:
   ```python
   @asset(group_name="<layer>", deps=["<upstream_asset>"])
   def <asset_name>(context: AssetExecutionContext) -> None:
       """One-line description."""
       settings = PipelineSettings()
       # ... logic
       context.add_output_metadata({"key": "value"})
   ```

3. **File naming**: follow `<type>_<function>.py` for any new utility files.

4. **Resources** (e.g. `DbtCliResource`): declare in function signature, already registered in `definitions.py`.

5. **Register**: `load_assets_from_modules` in `definitions.py` picks up the asset automatically if it's in the right module.

6. **Validate**:
   ```bash
   uv run dagster asset list          # should show the new asset
   uv run dagster asset materialize --select <asset_name>
   ```
