---
paths:
  - src/nephila/agent/**
  - tests/agent/**
---

# Agent — Architecture Context

## LangGraph ReAct State Machine

State defined in `model_state.py` (`AgentState` — TypedDict + `add_messages`).

```
START → [agent] ──► tool_calls? ──► [tools] ──► [agent] (loop)
                 └─► no tool_calls ──► [guardrail] ──► critical? ──► [warn] → END
                                                    └─► ok ──────► [response] → END
```

- **agent node**: LLM with bound tools (ReAct loop)
- **tools node**: `ToolNode` — runs whichever tool the LLM called
- **guardrail node**: mandatory before every final response — parses all ToolMessages for interaction levels
- **warn node**: blocks answer when `contre-indication` or `association déconseillée` is found
- **response node**: extracts `source_cis` from ToolMessages for traceability

## Tools (`agent/tools/`)

| File | LangChain tool | Data source |
|------|---------------|-------------|
| `tool_search_drug.py` | `search_drug` | ChromaDB `idx_bdpm_medicament_v1` |
| `tool_find_generics.py` | `find_generics` | Silver `silver_bdpm__generique` |
| `tool_check_interactions.py` | `check_interactions` | ChromaDB `idx_ansm_interaction_v1` |
| `tool_get_rcp.py` | `get_rcp` | Silver `silver_bdpm__info_importante` |

## Guardrails (non-negotiable)

- **No direct advice**: every response must reference the RCP (`silver_bdpm__info_importante`)
- **Interaction check mandatory**: guardrail runs before every final response
- **CIS traceability**: `source_cis` set in `AgentState` on every response
- **Self-hosted only**: ChromaDB local, no external cloud vector store

## AgentState fields

| Field | Type | Purpose |
|-------|------|---------|
| `messages` | `Annotated[list, add_messages]` | Full conversation (LangGraph managed) |
| `cis_codes` | `list[str]` | CIS codes mentioned in the conversation |
| `interactions_found` | `list[dict]` | Parsed from guardrail (`niveau_contrainte`, `detail`) |
| `interactions_checked` | `bool` | Set to `True` by guardrail node |
| `source_cis` | `str \| None` | First CIS extracted from ToolMessages |

## LangGraph Studio

```bash
uv run dotenv -f .env run -- uv run langgraph dev    # connect localhost:2024
```

Graph entrypoint declared in `langgraph.json` at project root.
