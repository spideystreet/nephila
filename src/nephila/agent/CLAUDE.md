# Agent — Architecture Context

## LangGraph ReAct State Machine

State defined in `model_state.py` (`AgentState` — Pydantic + `add_messages`).

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

## ChromaDB Index Naming

`idx_<source>_<content>_<model_version>` — e.g. `idx_bdpm_medicament_v1`, `idx_ansm_interaction_v1`

## LangGraph Studio (conversational UI)

```bash
# Install CLI (dev extra)
uv sync --extra dev

# Start local dev server (port 2024)
uv run langgraph dev

# Then open: https://smith.langchain.com/studio
# Connect to: http://localhost:2024
```

Requires in `.env`:
- `LANGCHAIN_API_KEY` — LangSmith API key
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_PROJECT=nephila`

Graph entrypoint declared in `langgraph.json` at project root.
