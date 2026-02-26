<div align="center">
  <img src="https://github.com/user-attachments/assets/1c252cae-6f46-4c70-93a8-7ab8e57c0da2" alt="Logo Nephila" width="200" />

  # Nephila

  <p>
    <img src="https://img.shields.io/badge/status-experimental-orange.svg" alt="Status Experimental">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/Agent-LangGraph-1C3C3C.svg" alt="LangGraph">
    <img src="https://img.shields.io/badge/Data-Dagster-715BB9.svg" alt="Dagster">
    <img src="https://img.shields.io/badge/Transform-dbt-FF694B.svg" alt="dbt">
  </p>
</div>

**Nephila** est un agent IA ReAct ultra-rapide conçu pour interroger les référentiels pharmaceutiques officiels français. 

> [!NOTE]
> **Disclaimer :** Nephila est un puissant outil d'information basé sur des données officielles ( ANSM, BDPM ), à titre expérimental. Il ne remplace absolument pas l'avis d'un professionnel de santé ( pour l'instant ).

## Ce qu'il fait de mieux
* 🔍 **Recherche instantanée** de médicaments (marques et génériques)
* 🔃 **Vérification automatique** des interactions entre substances actives
* 📄 **Consultation directe** des fiches RCP officielles

## Scaffold / Structure du repo
```text
nephila/
├── data/               # Données locales (couche Bronze)
├── dbt/                # Modèles et transformations SQL (couche Silver)
├── docs/               # Documentation du projet
├── src/nephila/        # Code source principal
│   ├── agent/          # Cerveau de l'IA (LangGraph, Tools, Nodes)
│   ├── models/         # Définition des schémas de données
│   └── pipeline/       # Orchestration Dagster (Assets, IO, Téléchargements)
├── docker-compose.yml  # Infrastructure locale
└── pyproject.toml      # Dépendances (Dagster, LangGraph, dbt...)
```
