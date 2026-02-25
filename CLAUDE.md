# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
uv sync                        # Installer les dépendances
uv sync --extra dev            # Avec les outils de dev
cp .env.example .env           # Config environnement

# PostgreSQL
docker compose up -d           # Démarrer PostgreSQL
docker compose down            # Arrêter

# Pipeline Dagster
uv run dagster dev             # Lancer l'UI Dagster (localhost:3000)
uv run dagster asset materialize --select bronze  # Matérialiser un groupe

# dbt
cd dbt && uv run dbt run       # Lancer les transformations Silver
cd dbt && uv run dbt test      # Tests dbt

# Lint & Type check
uv run ruff check src/         # Linter
uv run ruff format src/        # Formatter
uv run mypy src/               # Type checking

# Tests
uv run pytest                  # Tous les tests
uv run pytest tests/pipeline/  # Tests pipeline uniquement
uv run pytest tests/agent/     # Tests agent uniquement
```

---

## Project Overview

**Nephila** is a French HealthTech project: an intelligent agent (LangGraph) specialized in French drug repositories. It operates exclusively on official public data (BDPM, ANSM) and is designed for RGPD compliance and HDS certification readiness.

---

## Tech Stack

- **Language**: Python 3.11+, strict typing via Pydantic
- **Agent Orchestration**: LangGraph (state-driven architecture with cycles)
- **Data Pipeline**: Medallion architecture — Dagster (orchestration) + dbt (Silver SQL transforms) + Python
- **Vector DB**: ChromaDB (self-hosted, HDS-compatible — preferred over cloud providers)
- **Data Sources**: BDPM (public .txt files) + ANSM Thésaurus (PDF)

---

## Data Sources

| Source | URL | Format |
|--------|-----|--------|
| BDPM fichiers | https://www.data.gouv.fr/fr/datasets/base-donnees-publique-des-medicaments-bdpm/ | `.txt`, ISO-8859-1, tab-separated |
| ANSM Thésaurus interactions | https://ansm.sante.fr/documents/consultation/thesaurus-des-interactions-medicamenteuses | PDF (parsing requis) |

---

## Data Pipeline — Medallion

### Bronze (Raw ingestion)
Raw `.txt` files ingested as-is. Encoding: **ISO-8859-1**, separator: **tabulation**.

Key BDPM files and their column mapping (0-indexed):

| Fichier | Colonnes clés |
|---------|---------------|
| `CIS_bdpm.txt` | [0] CIS, [1] Dénomination, [2] Forme pharma, [3] Voies admin, [6] État commercialisation, [10] Titulaire |
| `CIS_CIP_bdpm.txt` | [0] CIS, [1] Code CIP7, [2] Libellé présentation, [6] Code CIP13, [8] État commercialisation |
| `CIS_COMPO_bdpm.txt` | [0] CIS, [1] Désignation élément, [2] Code substance, [3] Dosage |
| `CIS_GENER_bdpm.txt` | [0] ID Groupe, [1] Libellé, [2] CIS, [3] Type générique |
| `CIS_CPD_bdpm.txt` | [0] CIS, [1] Condition de prescription/délivrance |
| `CIS_InfoImportantes.txt` | [0] CIS, [1] Lien RCP/notice |

Pour le Thésaurus ANSM : parsing PDF via `pdfplumber` ou `camelot` avant ingestion Bronze.

### Silver (Cleaned SQL via dbt)
Normalized relational tables, deduplication, FK constraints CIS→CIP.

### Gold (Vector Embeddings — ChromaDB)
Metadata filtering obligatoire sur **code CIS** (spécialité) et **code CIP13** (présentation/boîte).

> **Distinction CIS vs CIP** : CIS identifie la spécialité (médicament), CIP identifie la présentation physique (boîte). Les deux servent de clés de filtrage vectoriel.

---

## Agent Architecture (LangGraph)

State-driven avec cycles. Nœuds principaux :

1. **Retrieval** — Requête ChromaDB avec filtrage CIS/CIP
2. **Interaction Check** *(guardrail obligatoire)* — Vérification Thésaurus ANSM avant chaque réponse ; implémenté comme **conditional edge** pour court-circuiter la réponse si interaction détectée
3. **Response** — Réponse citant le RCP, jamais de conseil direct

---

## Security & Compliance Guardrails

- **Pas de conseil direct** : toute réponse doit référencer le RCP (via `CIS_InfoImportantes.txt`)
- **Nœud interaction obligatoire** : le Thésaurus ANSM est vérifié avant chaque réponse finale
- **Traçabilité** : le code CIS doit être présent dans les métadonnées de chaque réponse
- **RGPD/HDS scope** : la donnée BDPM est publique (hors périmètre). Le périmètre RGPD concerne les **queries utilisateurs et les logs agent** — anonymisation et rétention à définir
- **Self-hosted uniquement** : pas de services cloud externes pour les données (ChromaDB local, pas Pinecone)

---

## Git Conventions

### Commits
- **Author** : spideystreet &lt;dhicham.pro@gmail.com&gt;
- **Co-Author** : spidecode-bot &lt;263227865+spicode-bot@users.noreply.github.com&gt;

Toujours inclure le co-auteur dans le message de commit :
```
Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
```

### Pull Requests
- **Author** : spicode-bot
- **Reviewer** : spideystreet
