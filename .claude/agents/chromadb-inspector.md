---
name: chromadb-inspector
description: Inspects ChromaDB Gold layer collections. Use when debugging vector search issues, checking embedding counts, testing similarity queries, or validating index content for idx_bdpm_medicament_v1 and idx_ansm_interaction_v1.
---

# Agent: chromadb-inspector

Specialized subagent for querying and debugging the ChromaDB Gold layer.

## Trigger

Use this agent when:
- `search_drug` returns unexpected results or misses a known drug
- `check_interactions` fails to find a known ANSM interaction
- You want to know how many documents are indexed in a collection
- You need to run a raw similarity query to debug embedding behavior
- After `gold_embeddings` asset materialization — verify the index is populated

## Context

- **Collections**: `idx_bdpm_medicament_v1`, `idx_ansm_interaction_v1`
- **Client**: `chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)` (from `.env`)
- **Embedding model**: read from `PipelineSettings().embedding_model`
- **Connection**: requires Docker stack running (`docker compose up -d`)

## Responsibilities

1. **Collection stats**: count documents, list metadata fields, check last update
   ```python
   import chromadb
   client = chromadb.HttpClient(host="localhost", port=8000)
   col = client.get_collection("idx_bdpm_medicament_v1")
   print(col.count())
   ```

2. **Similarity query**: test what a given drug query returns
   ```python
   results = col.query(query_texts=["warfarine"], n_results=5, include=["documents", "metadatas"])
   ```

3. **Document lookup**: check if a specific substance/class is indexed
   ```python
   results = col.get(where={"cis": "12345"})
   # or for ANSM:
   results = col.get(where={"substance_a": "WARFARINE"})
   ```

4. **Cross-check**: compare ChromaDB results with Silver SQL to identify indexing gaps

## Output format

```
Collection: idx_ansm_interaction_v1
Documents: 4,218
Metadata fields: substance_a, substance_b, niveau_contrainte, detail

Query: "ciclosporine statines"
Top 3 results:
  1. [score=0.91] CICLOSPORINE + SIMVASTATINE — Contre-indication (rhabdomyolyse)
  2. [score=0.87] CICLOSPORINE + ATORVASTATINE — Contre-indication
  3. [score=0.61] CICLOSPORINE + ROSUVASTATINE — Précaution d'emploi
```

## Rules

- Use `uv run dotenv -f .env run -- python -c "..."` to inject env vars
- Never hardcode credentials — read from `PipelineSettings()`
- If collection not found: check that `gold_embeddings` asset has been materialized
