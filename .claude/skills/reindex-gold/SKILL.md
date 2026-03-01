---
name: reindex-gold
description: Rebuild ChromaDB Gold layer indexes after source data changes. Invoke manually — deletes and recreates collections, do NOT trigger automatically.
disable-model-invocation: true
---

# Skill: Rebuild the ChromaDB Gold Index

Use when: BDPM/ANSM source data has changed, Silver models were updated, or ChromaDB collections are missing/stale.

## Steps

1. **Ensure Docker stack is running**:
   ```bash
   docker compose up -d
   docker ps    # verify chromadb and postgres containers are healthy
   ```

2. **Ensure Silver is up to date** (run if source data changed):
   ```bash
   uv run dotenv -f dbt/.env run -- uv run dbt run --project-dir dbt --profiles-dir dbt
   uv run dotenv -f dbt/.env run -- uv run dbt test --project-dir dbt --profiles-dir dbt
   ```

3. **Materialize the Gold asset**:
   ```bash
   uv run dotenv -f .env run -- uv run dagster asset materialize --select gold_embeddings
   ```

4. **Verify collections** via chromadb-inspector agent or directly:
   ```bash
   uv run dotenv -f .env run -- python -c "
   import chromadb, os
   c = chromadb.HttpClient(host=os.environ['CHROMA_HOST'], port=int(os.environ['CHROMA_PORT']))
   for name in ['idx_bdpm_medicament_v1', 'idx_ansm_interaction_v1']:
       print(name, c.get_collection(name).count())
   "
   ```

5. **Smoke-test the agent tools**:
   ```bash
   uv run dotenv -f .env run -- python -c "
   from nephila.agent.tools.tool_search_drug import search_drug
   from nephila.agent.tools.tool_check_interactions import check_interactions
   print(search_drug.invoke({'query': 'doliprane'}))
   print(check_interactions.invoke({'substance_a': 'warfarine', 'substance_b': 'ibuprofene'}))
   "
   ```

## Collection naming

| Collection | Content | Rebuilt from |
|------------|---------|--------------|
| `idx_bdpm_medicament_v1` | Drug denominations + metadata | `silver_bdpm__medicament` |
| `idx_ansm_interaction_v1` | ANSM interaction pairs | `silver_ansm__interaction` |

## Rules

- Always run dbt tests before reindexing — bad Silver data produces bad embeddings
- Full reindex deletes and recreates the collection — expect a few minutes
- If `gold_embeddings` fails: check `CHROMA_HOST`/`CHROMA_PORT` in `.env` and Docker status
