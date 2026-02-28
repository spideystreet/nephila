---
paths:
  - tests/**
---

# Test Conventions

## Framework

pytest — config in `pyproject.toml` → `[tool.pytest.ini_options]`.
Shared fixtures in `tests/conftest.py`.

## Markers

| Marker | Meaning | Requires |
|--------|---------|---------|
| *(none)* | Pure unit test | Nothing — runs anywhere |
| `@pytest.mark.integration` | Hits PostgreSQL or ChromaDB | Docker stack up |

Always mark tests that open a DB connection or call ChromaDB with `@pytest.mark.integration`.

## Running tests

```bash
# All tests (Docker must be up for integration tests)
uv run pytest

# Unit tests only — no Docker needed
uv run pytest -m "not integration"

# Specific suite
uv run pytest tests/agent/ -v
uv run pytest tests/pipeline/ -v
```

## Test structure

```
tests/
├── conftest.py          # Shared fixtures (add here, not per-file)
├── agent/               # Agent node + tool unit tests
├── pipeline/            # Pipeline parser unit tests
└── e2e/                 # prompts.yaml — LangSmith eval (run via scripts/run_eval.py)
```

## Conventions

- **Class-based**: `class TestXxx` — one class per function/node under test
- **Method names**: `test_<scenario>` — describe the behaviour, not the implementation
- **State helpers**: use a local `_state(...)` function to build minimal dicts — do not import fixtures for this
- **No mocks for unit tests**: test real logic with minimal state inputs; if you need a mock, it's probably an integration test
- **Tool tests**: test input validation (no marker) separately from DB queries (`@pytest.mark.integration`)
- **One assertion focus per test**: each test should fail for one clear reason
- **Docstring on non-obvious tests**: one line explaining the invariant being tested

## What goes where

| What | Where |
|------|-------|
| New node test | `tests/agent/test_node_<name>.py` |
| New tool test | `tests/agent/test_tool_<name>.py` |
| New pipeline component | `tests/pipeline/test_<name>.py` |
| New e2e eval case | `tests/e2e/prompts.yaml` (see `/add-eval-case`) |
