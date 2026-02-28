---
paths:
  - dbt/**
---

# dbt — Conventions & Context

## Model Naming

`<layer>_<source>__<entity>.sql`

Examples: `silver_bdpm__medicament.sql`, `silver_ansm__interaction.sql`

## Contract = One Model = One `.yml`

Each `.sql` model has a matching `.yml` contract with the **same name**:
```
silver_bdpm__medicament.sql   ←→   silver_bdpm__medicament.yml
```
No shared `schema.yml`. The `.yml` is the contract: columns, descriptions, data tests.

## Macros

Use macros for any transformation used more than once. Existing macros in `dbt/macros/`:

| Macro | Usage |
|-------|-------|
| `clean_text(col)` | `NULLIF(TRIM(col), '')` |
| `parse_bdpm_date(col)` | `TO_DATE(NULLIF(TRIM(col), ''), 'DD/MM/YYYY')` |
| `is_valid_cis(col)` | `col IS NOT NULL AND col ~ '^[0-9]+$'` |

## Sources

All raw tables declared in `dbt/models/sources.yml` under source `raw`.
Reference with `{{ source('raw', 'table_name') }}`.

## Current Silver Models

`silver_bdpm__`: medicament, presentation, composition, substance, groupe_generique, generique, condition_delivrance, info_importante
`silver_ansm__`: interaction

## Singular Tests (`dbt/tests/`)

Each singular test SQL file has a matching `.yml` contract with the **same name**:
```
dbt/tests/silver_ansm__interaction__niveau_contrainte_valid.sql
  ←→ dbt/tests/silver_ansm__interaction__niveau_contrainte_valid.yml
```

YAML contract format:
```yaml
version: 2

singular_tests:
  - name: <test_name>
    description: >
      <What invariant this enforces and why it matters.>
    model: <model_ref>
    column: <column_name>
    failure: >
      <What a non-empty result set means — what rows are returned and why they're wrong.>
```

Naming convention: `<model_name>__<column>__<invariant>.sql`

## Layer Config (`dbt_project.yml`)

Silver models → schema `silver`, materialized `table`.
