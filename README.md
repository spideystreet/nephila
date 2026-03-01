<div align="center">
  <img src="docs/favicon.png" alt="Logo Nephila" width="200" />

  # Nephila

  <p>
    <img src="https://img.shields.io/badge/status-experimental-orange.svg" alt="Status Experimental">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/Agent-LangGraph-1C3C3C.svg" alt="LangGraph">
    <img src="https://img.shields.io/badge/Data-Dagster-715BB9.svg" alt="Dagster">
    <img src="https://img.shields.io/badge/Transform-dbt-FF694B.svg" alt="dbt">
  </p>
</div>

**Nephila** is a fast ReAct AI agent built to query official French pharmaceutical databases.

> [!NOTE]
> **Disclaimer:** Nephila is an experimental information tool based on official data — ANSM, BDPM. It does not replace professional medical advice.

## Features
* 🔍 **Instant drug search** across brand names and generics
* 🔃 **Automatic interaction checking** between active substances
* 📄 **Direct access** to official RCP — Summary of Product Characteristics

## Quickstart

```bash
# 1. Install dependencies
uv sync && uv sync --extra dev
cp .env.example .env          # fill in required variables

# 2. Start infrastructure
docker compose up -d           # PostgreSQL + ChromaDB

# 3. Load data — Bronze → Silver → Gold
uv run dotenv -f .env run -- uv run dagster dev              # localhost:3000
uv run dotenv -f .env run -- uv run dagster asset materialize --select '*'

# 4. Launch the agent
uv run dotenv -f .env run -- uv run langgraph dev   # Studio at localhost:2024
```

## Repository structure
```text
nephila/
├── data/                # Local files — Bronze layer
├── dbt/                 # SQL models & transforms — Silver layer
├── docs/                # Mintlify documentation
├── scripts/             # Utility scripts — run_eval.py
├── src/nephila/         # Main source code
│   ├── agent/           # LangGraph ReAct agent
│   │   ├── nodes/       # Graph nodes — guardrail, response, warn
│   │   ├── tools/       # LangChain tools — search, interactions, generics, RCP
│   │   ├── queries.py   # Typed SQL queries — Pydantic-validated
│   │   └── graph_agent.py
│   ├── models/          # Pydantic schemas — ANSM, BDPM, query results
│   └── pipeline/        # Dagster orchestration — assets, loaders, parsers
├── tests/               # pytest — unit + integration + e2e eval
├── docker-compose.yml   # PostgreSQL + ChromaDB
└── pyproject.toml       # Dependencies — LangGraph, Dagster, dbt...
```
