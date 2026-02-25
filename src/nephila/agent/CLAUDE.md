# Agent — Architecture Context

## LangGraph State Machine

State defined in `agent/model_state.py` (`AgentState` — Pydantic + `add_messages`).

```
User query
    │
    ▼
[retrieval]  ──►  ChromaDB query (filter by CIS / CIP13)
    │
    ▼
[interaction_check]  ──►  ANSM Thésaurus lookup        ← mandatory guardrail
    │                           │
    │ no interaction             │ interaction detected
    ▼                           ▼
[response]               [block / warn response]
```

`interaction_check` is a **conditional edge** — it short-circuits to a warning response if an interaction is detected before any answer is emitted.

## Nodes (to implement in `agent/nodes/`)

| Node file | Role |
|-----------|------|
| `node_retrieval.py` | Query ChromaDB with CIS/CIP13 metadata filter |
| `node_interaction_check.py` | Check ANSM Thésaurus (Silver `silver_ansm__interaction`) |
| `node_response.py` | Format answer citing RCP — never direct medical advice |

## Guardrails (non-negotiable)

- **No direct advice**: every response must reference the RCP (`silver_bdpm__info_importante`)
- **Interaction check mandatory**: run before every final response
- **CIS traceability**: `source_cis` must be set in `AgentState` metadata on every response
- **RGPD scope**: user queries and agent logs — apply anonymization + retention policy (BDPM data itself is public)
- **Self-hosted only**: ChromaDB local, no external cloud vector store

## ChromaDB Index Naming

`idx_<source>_<content>_<model_version>` — e.g. `idx_bdpm_medicament_v1`, `idx_ansm_interactions_v1`
