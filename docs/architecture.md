# Architecture

## Flux de données

```mermaid
flowchart LR
  subgraph Sources ouvertes
    DECP[DECP consolidées<br/>decp.info · data.gouv.fr]
    BOAMP[BOAMP<br/>API DILA]
    SIRENE[API Recherche<br/>d'entreprises]
    REF[CPV 2008 · COG INSEE<br/>IGN Admin Express]
  end
  subgraph Entrepôt DuckDB + dbt
    STG[staging] --> INT[intermediate<br/>règles de nettoyage]
    INT --> MARTS[marts<br/>modèle en étoile]
  end
  DECP --> STG
  REF --> STG
  SIRENE --> INT
  BOAMP --> PARSE[radar.boamp<br/>aplatissement multi-schéma]
  MARTS --> SEM[Couche sémantique<br/>semantic/metrics.yml]
  MARTS --> HIST[Historique compact<br/>data/history]
  PARSE --> RADAR[Radar AO<br/>BM25 + embeddings + signaux DECP]
  HIST --> RADAR
  SEM --> EXPORT[Exports du site<br/>cube Parquet, JSON]
  RADAR --> EXPORT
  EXPORT --> SITE[Site statique<br/>React · GitHub Pages]
  RADAR --> API[Application locale<br/>FastAPI]
  API --> SITE
```

## Modèle en étoile

```mermaid
erDiagram
  fct_attributions }o--|| dim_acheteur : acheteur_id
  fct_attributions }o--|| dim_titulaire : titulaire_key
  fct_attributions }o--|| dim_cpv : code_cpv
  fct_attributions }o--|| dim_date : date_key
  fct_attributions }o--|| dim_geo : departement_code
  fct_attributions }o--|| dim_procedure : procedure_code
  fct_attributions {
    string attribution_id PK
    string marche_uid
    double montant_marche
    double montant_part
    int offres_recues
    double poids_marche
  }
```

Grain : une attribution initiale = un marché × un titulaire. `montant_part` répartit le montant entre co-titulaires ; `poids_marche` (1 / nombre de titulaires) permet de compter les marchés de façon additive.

## Lignage dbt

```mermaid
flowchart LR
  raw_decp[(raw.decp)] --> stg_decp__attributions --> int_attributions
  raw_cpv[(raw.cpv)] --> stg_ref__cpv --> dim_cpv
  raw_geo[(raw.geo)] --> stg_ref__geo --> dim_geo
  raw_sirene[(raw.sirene)] --> stg_sirene__unites --> int_titulaires
  int_attributions --> int_titulaires --> dim_titulaire
  int_attributions --> int_concurrence_acheteur_cpv
  int_attributions --> dim_acheteur
  int_attributions --> fct_attributions
  dim_cpv --> fct_attributions
  int_titulaires --> fct_attributions
  procedures[(seed procedures)] --> dim_procedure
  fct_attributions --> mart_marches
  dim_date --> mart_marches
```

La documentation dbt complète (descriptions, tests, lignage interactif) se génère avec `make dbt-docs` puis `cd dbt && ../.venv/bin/dbt docs serve --profiles-dir .`.

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `pipeline/radar/` | Téléchargement, parseur BOAMP, SIRENE, couche sémantique, scoring, évaluation, exports, API |
| `dbt/` | Projet dbt (staging, intermediate, marts, tests, seeds) |
| `semantic/` | Définitions des indicateurs |
| `config/` | Profils fictifs et poids du score |
| `data/` | Données compactes versionnées : référentiels, instantané BOAMP, historique, empreintes des sources |
| `web/` | Site React (Vite, TypeScript, ECharts, motion) |
| `tests/` | Tests pytest |
| `docs/` | Démarche BA, rapports générés, captures |
