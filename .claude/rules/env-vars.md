# Environment Variables

## Terminal — always use dotenv CLI

Never use `export VAR=...` or `set -a && source .env`.
Always use `dotenv` via:
```bash
uv run dotenv -f <path>/.env run -- <command>
```

`dotenv` is not in the system PATH — always prefix with `uv run`.
dbt has its own `.env` in `dbt/.env`.

If a variable is missing: report it to the user, never set it manually.

## Env loading in code

Use `load_dotenv()` from `python-dotenv` at entrypoint.
Never use `SettingsConfigDict(env_file=".env")` — `BaseSettings` reads from `os.environ`.

## Required variables

| Component  | Variables |
|------------|-----------|
| PostgreSQL | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD` |
| ChromaDB   | `CHROMA_HOST`, `CHROMA_PORT` |
| LangSmith  | `LANGSMITH_API_KEY`, `LANGSMITH_TRACING=true`, `LANGSMITH_PROJECT=nephila` |
| LLM        | `OPENAI_API_KEY` (or `OPENROUTER_API_KEY` + `OPENROUTER_BASE_URL`) |

See `.env.example` for the full list.
