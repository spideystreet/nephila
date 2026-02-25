# Pipeline — Architecture Context

## Medallion Overview

```
Bronze  →  Raw files on disk          data/bronze/{bdpm/, ansm/}
Silver  →  Normalized SQL             PostgreSQL schemas: raw → silver (via dbt)
Gold    →  Vector embeddings          ChromaDB (self-hosted)
```

Orchestration: **Dagster**. Transformations: **dbt + Python**.

## Asset Graph

```
bdpm_raw ──────────┐
                   ├──► bdpm_to_raw ──┐
ansm_thesaurus_raw ─► ansm_to_raw ───┴──► silver_dbt ──► gold_embeddings
```

## Python Naming

`<type>_<function>.py` — e.g. `asset_bronze.py`, `loader_bdpm.py`, `parser_ansm.py`, `model_bdpm.py`, `config_pipeline.py`

## Key Files

| File | Role |
|------|------|
| `pipeline/config_pipeline.py` | `PipelineSettings` — all env vars via `load_dotenv()` |
| `pipeline/io/downloader_bdpm.py` | HTTP download — BDPM .txt + ANSM PDF scraper |
| `pipeline/io/loader_bdpm.py` | Bulk-load .txt → PostgreSQL `raw` schema (pandas + SQLAlchemy) |
| `pipeline/io/parser_ansm.py` | pdfplumber heuristic parser for ANSM Thésaurus |
| `pipeline/assets/asset_{bronze,silver,gold}.py` | Dagster assets per layer |
| `pipeline/definitions.py` | Dagster `Definitions` entrypoint + resources |

## BDPM File Mapping

Source encoding: **ISO-8859-1**, separator: **tab**. Column names defined in `loader_bdpm.BDPM_FILE_COLUMNS`.

| File | Raw table | Key columns |
|------|-----------|-------------|
| `CIS_bdpm.txt` | `raw.cis_bdpm` | cis, denomination, forme_pharma, etat_commercialisation |
| `CIS_CIP_bdpm.txt` | `raw.cis_cip_bdpm` | cis, cip7, cip13, libelle_presentation |
| `CIS_COMPO_bdpm.txt` | `raw.cis_compo_bdpm` | cis, code_substance, dosage, nature_composant |
| `CIS_GENER_bdpm.txt` | `raw.cis_gener_bdpm` | id_groupe, cis, type_generique |
| `CIS_CPD_bdpm.txt` | `raw.cis_cpd_bdpm` | cis, condition_prescription_delivrance |
| `CIS_InfoImportantes.txt` | `raw.cis_infoimportantes` | cis, texte_info_importante (RCP link) |

## Rules

- No default values for sensitive vars (passwords, keys, usernames, db names) — in code, docker-compose, or dbt profiles
- Non-sensitive vars (host, port) may have defaults
- `load_dotenv()` at entrypoint, never `SettingsConfigDict(env_file=...)`
