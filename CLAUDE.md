# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
uv sync && uv sync --extra dev
cp .env.example .env

# Docker
docker compose up -d           # PostgreSQL + ChromaDB
docker compose down

# Dagster
uv run dagster dev             # UI at localhost:3000
uv run dagster asset materialize --select bronze

# dbt (run from repo root)
uv run dbt run --project-dir dbt --profiles-dir dbt
uv run dbt test --project-dir dbt --profiles-dir dbt

# Quality
uv run ruff check src/
uv run ruff format src/
uv run mypy src/
uv run pytest
uv run pytest tests/pipeline/ -v
```

---

## Git Conventions

### Commits
- **Author**: spideystreet <dhicham.pro@gmail.com>
- **Co-Author**: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>

Always include in commit message:
```
Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
```

### Pull Requests
- **Author**: spicode-bot — **Reviewer**: spideystreet

---

## Architecture

@src/nephila/pipeline/CLAUDE.md
@src/nephila/agent/CLAUDE.md
@dbt/CLAUDE.md
