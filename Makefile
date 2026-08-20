# Radar Marchés Publics — commandes du projet.
# `make help` liste les cibles. Prérequis : Python 3.12+, uv, Node.js 20+.

PY      := .venv/bin/python
DBT     := cd dbt && ../.venv/bin/dbt
RUN     := cd pipeline && ../$(PY) -m
SNAPSHOT ?=

.DEFAULT_GOAL := help
.PHONY: help install data data-reference boamp sirene dbt dbt-docs quality history pipeline evaluate site test lint screenshots app all clean

help: ## Affiche cette aide
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[1m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Installe l'environnement Python (uv) et les dépendances du site (npm)
	uv venv -q --allow-existing -p 3.12 .venv
	uv pip install -q -p .venv -e ".[dev]"
	cd web && npm ci

data: ## Télécharge les sources (DECP figée par sources.lock.json, CPV, géographie, carte) et aplatit le BOAMP versionné
	$(RUN) radar.download decp
	$(RUN) radar.download cpv
	$(RUN) radar.download geo
	$(RUN) radar.download carte
	@if [ ! -f data/interim/boamp_avis.parquet ]; then cp $$(ls data/snapshots/boamp_avis_*.parquet | tail -1) data/interim/boamp_avis.parquet; fi
	@if [ ! -f data/interim/sirene.parquet ]; then cd pipeline && ../$(PY) -c "import pandas as pd; from radar import config; pd.read_parquet(config.DATA / 'history' / 'sirene_titulaires.parquet').to_parquet(config.INTERIM / 'sirene.parquet', index=False)"; fi

boamp: ## Prend un nouvel instantané des avis BOAMP ouverts (remplace l'instantané de la démo)
	$(RUN) radar.download boamp
	$(RUN) radar.boamp

sirene: ## Enrichit les 3 000 principaux titulaires via l'API Recherche d'entreprises (avec cache)
	$(RUN) radar.sirene --max 3000

dbt: ## Construit l'entrepôt DuckDB et exécute les tests dbt
	$(DBT) seed --profiles-dir . -q
	$(DBT) build --profiles-dir .

dbt-docs: ## Génère la documentation dbt (lignage) dans dbt/target
	$(DBT) docs generate --profiles-dir .

quality: ## Rapport de qualité des données (docs/qualite-donnees.md)
	$(RUN) radar.quality

history: ## Extraits historiques compacts utilisés par le radar (data/history)
	$(RUN) radar.history

evaluate: ## Évaluation du radar (docs/evaluation-radar.md), environ 10 minutes sur CPU
	$(RUN) radar.evaluate

pipeline: dbt quality history ## Entrepôt + qualité + historique + exports du site
	$(RUN) radar.export_site

site: ## Construit le site statique (web/dist)
	cd web && npm run build

test: lint ## Lint + tests Python (pytest) et tests du front (Vitest) ; les tests dbt passent avec `make dbt`
	$(PY) -m pytest -q
	cd web && npx vitest run

lint: ## Vérifications statiques (ruff, TypeScript)
	.venv/bin/ruff check pipeline tests
	.venv/bin/ruff format --check pipeline tests
	cd web && npx tsc -b

screenshots: site ## Captures Playwright des pages (docs/img)
	cd web && node scripts/screenshots.mjs ../docs/img
	$(PY) scripts/optimise_images.py docs/img

app: site ## Lance l'application locale sur http://127.0.0.1:8000/radar-marches-publics/
	cd pipeline && ../.venv/bin/uvicorn radar.api:app --port 8000

all: install data pipeline evaluate site test screenshots ## Chaîne complète, des sources aux captures

clean: ## Supprime les artefacts régénérables (entrepôt, caches, build)
	rm -rf data/warehouse data/interim dbt/target dbt/logs web/dist
