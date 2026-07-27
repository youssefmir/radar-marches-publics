"""Chemins et paramètres partagés par le pipeline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
REFERENCE = DATA / "reference"
SNAPSHOTS = DATA / "snapshots"
INTERIM = DATA / "interim"
CACHE = DATA / "cache"
WAREHOUSE = DATA / "warehouse" / "radar.duckdb"
SITE_DATA = ROOT / "web" / "public" / "data"
SEMANTIC = ROOT / "semantic" / "metrics.yml"
SOURCES_LOCK = ROOT / "data" / "sources.lock.json"

# Période d'analyse retenue pour l'historique des attributions (date de notification).
PERIOD_START = "2021-01-01"

# Identifiant data.gouv.fr du jeu « DECP consolidées (format tabulaire) » publié par decp.info.
DECP_DATASET = "donnees-essentielles-de-la-commande-publique-consolidees-format-tabulaire"
DECP_RESOURCE_TITLE = "decp.parquet"

BOAMP_API = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp"
CPV_API = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/nomenclature-cpv"
GEO_API = "https://geo.api.gouv.fr"
SIRENE_API = "https://recherche-entreprises.api.gouv.fr/search"

for d in (RAW, REFERENCE, SNAPSHOTS, INTERIM, CACHE, WAREHOUSE.parent):
    d.mkdir(parents=True, exist_ok=True)
