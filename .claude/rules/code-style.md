# Code Style & Conventions

## Language

All code comments, docstrings, and documentation must be in **English**.

## Python naming

`<type>_<function>.py` — e.g. `asset_bronze.py`, `loader_bdpm.py`, `parser_ansm.py`

## No secrets as defaults

Never hardcode default values for sensitive variables (passwords, API keys, usernames, database names):
- Not in Python code
- Not in `docker-compose.yml`
- Not in dbt profiles

Use `env_var('VAR')` without fallback in dbt, `${VAR}` without `:-default` in Docker.
Non-sensitive vars (host, port) may have defaults.

## ChromaDB index naming

`idx_<source>_<content>_<model_version>` — e.g. `idx_bdpm_medicament_v1`, `idx_ansm_interaction_v1`
