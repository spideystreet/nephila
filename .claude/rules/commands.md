# Dev Commands

## Setup
```bash
uv sync && uv sync --extra dev
cp .env.example .env
```

## Docker
```bash
docker compose up -d    # PostgreSQL + ChromaDB
docker compose down
```

## Dagster
```bash
uv run dotenv -f .env run -- uv run dagster dev                              # UI at localhost:3000
uv run dotenv -f .env run -- uv run dagster asset materialize --select bronze
```

## dbt (run from repo root)
```bash
uv run dotenv -f dbt/.env run -- uv run dbt run --project-dir dbt --profiles-dir dbt
uv run dotenv -f dbt/.env run -- uv run dbt test --project-dir dbt --profiles-dir dbt
```

## LangGraph Studio
```bash
uv run dotenv -f .env run -- uv run langgraph dev    # UI at smith.langchain.com/studio → connect localhost:2024
```

## Quality
```bash
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/
uv run sqlfluff lint dbt/models/ dbt/tests/ --config dbt/.sqlfluff

# Or use /lint to run all linters at once

# Tests — unit only (no Docker needed)
uv run pytest -m "not integration"

# Tests — full suite (Docker must be up)
uv run pytest

# Specific suite
uv run pytest tests/agent/ -v
uv run pytest tests/pipeline/ -v
```

## Evaluation
```bash
uv run dotenv -f .env run -- python scripts/run_eval.py
```
