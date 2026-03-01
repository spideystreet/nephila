# Nephila

Medical drug interaction assistant for French Healthcare professionals. 
LangGraph ReAct agent over BDPM + ANSM data.

## Tech Stack

Python · LangGraph · LangChain · Dagster · dbt · PostgreSQL · ChromaDB (self-hosted)

## Architecture

```
Bronze (raw files) → Silver (PostgreSQL via dbt) → Gold (ChromaDB embeddings)
                                                          ↓
                                              LangGraph ReAct Agent
```

## Key directories

| Path | Role |
|------|------|
| `src/nephila/agent/` | LangGraph agent, nodes, tools |
| `src/nephila/pipeline/` | Dagster assets, loaders, parsers |
| `dbt/` | dbt Silver models + contracts |
| `tests/` | pytest unit + e2e eval (`prompts.yaml`) |
| `scripts/` | `run_eval.py` — LangSmith evaluation |
