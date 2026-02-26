# GEMINI.md

This file provides the contextual mandates and operational guidelines for Gemini CLI when working on the **Nephila** project.

## Project Overview

**Nephila** is an ultra-fast AI agent (ReAct) designed to query official French pharmaceutical repositories (ANSM and BDPM). It uses a Medallion architecture to process raw data into normalized SQL tables and vector embeddings for semantic search.

### Core Technologies
- **Agent Framework:** LangGraph (ReAct state machine).
- **Data Orchestration:** Dagster.
- **SQL Transformations:** dbt (PostgreSQL).
- **Vector Database:** ChromaDB (self-hosted).
- **Language:** Python 3.11+ (managed via `uv`).
- **Embeddings:** `intfloat/multilingual-e5-base` (local).

### Architecture (Medallion)
- **Bronze Layer:** Raw files (BDPM .txt and ANSM PDFs) stored in `data/bronze/`.
- **Silver Layer:** Normalized SQL tables in PostgreSQL (schema `silver`), transformed via dbt.
- **Gold Layer:** Vector embeddings in ChromaDB (schema `gold`).

---

## Building and Running

### Setup
```bash
# Install dependencies
uv sync && uv sync --extra dev

# Configuration
cp .env.example .env

# Infrastructure (PostgreSQL + ChromaDB)
docker compose up -d
```

### Data Pipeline
```bash
# Launch Dagster UI (localhost:3000)
uv run dagster dev

# Materialize Bronze layer (direct CLI)
uv run dagster asset materialize --select bronze

# Run dbt transformations (from root)
uv run dbt run --project-dir dbt --profiles-dir dbt
```

### Testing and Quality
```bash
# Run all tests
uv run pytest

# Linting and Formatting
uv run ruff check src/
uv run ruff format src/

# Type Checking
uv run mypy src/
```

---

## Development Conventions

### General Rules
- **Python Naming:** Use `<type>_<function>.py` (e.g., `asset_bronze.py`, `loader_bdpm.py`, `tool_search_drug.py`).
- **Configuration:** Use `PipelineSettings` in `src/nephila/pipeline/config_pipeline.py`. Use `load_dotenv()` at the entry point.
- **Security:** Never commit secrets or default passwords. Avoid hardcoding sensitive variables in `docker-compose.yml` or `dbt/profiles.yml`.
- **Git Commits:** Always include the co-author in the commit message:
  ```
  Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
  ```

### Agent Mandates (src/nephila/agent/)
- **Mandatory Guardrails:** Every response must pass through the `guardrail` node to check for interactions.
- **Traceability:** Every response must include `source_cis` and reference the official RCP (Summary of Product Characteristics).
- **No Direct Advice:** The agent is an information tool; it must never replace a healthcare professional.
- **Vector Store:** Always use the local ChromaDB instance (`idx_<source>_<content>_<v>`).

### dbt Mandates (dbt/)
- **Model Naming:** `<layer>_<source>__<entity>.sql` (e.g., `silver_bdpm__medicament.sql`).
- **Contract:** Each `.sql` model MUST have a corresponding `.yml` file with the same name containing its contract (columns, descriptions, tests).
- **Sources:** Always use `{{ source('raw', 'table_name') }}` for tables in the `raw` schema.

---

## Directory Structure

- `data/`: Local storage for raw and intermediate files.
- `dbt/`: dbt project (models, macros, tests).
- `docs/`: Documentation (Mintlify format).
- `src/nephila/`: Main package.
  - `agent/`: LangGraph logic, tools, and nodes.
  - `models/`: Data schema definitions (Pydantic/SQLAlchemy).
  - `pipeline/`: Dagster definitions, assets, and IO logic.
- `tests/`: Project tests (pytest).
