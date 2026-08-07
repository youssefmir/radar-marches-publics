"""Enrichissement SIRENE des titulaires via l'API Recherche d'entreprises (sans clé).

- Périmètre : les titulaires identifiés par un SIRET valide, classés par montant attribué,
  dans la limite de `--max` (par défaut 3 000) : l'enrichissement est donc PARTIEL et documenté.
- Débit : l'API autorise 7 requêtes/s ; on reste en dessous (≈ 4 req/s) avec réessais.
- Cache : data/cache/sirene.jsonl (une ligne par SIREN), relu à chaque exécution.

Usage : python -m radar.sirene [--max 3000]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import duckdb
import pandas as pd

from . import config
from .net import get_json

CACHE_FILE = config.CACHE / "sirene.jsonl"
OUT = config.INTERIM / "sirene.parquet"
COLUMNS = [
    "siren",
    "nom_complet",
    "categorie_entreprise",
    "tranche_effectif",
    "nature_juridique",
    "est_entrepreneur_individuel",
    "activite_principale",
    "region_siege",
    "etat_administratif",
    "date_creation",
    "retrieved_at",
]

_lock = threading.Lock()
_last_call = [0.0]
MIN_INTERVAL = 0.25  # secondes entre deux appels (≈ 4 req/s)


def _throttle() -> None:
    with _lock:
        wait = _last_call[0] + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()


def parse_result(siren: str, payload: dict | None) -> dict:
    """Extrait les champs utiles d'une réponse de l'API (ou un enregistrement vide si non trouvé)."""
    now = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    hit = None
    for r in (payload or {}).get("results", []):
        if r.get("siren") == siren:
            hit = r
            break
    if hit is None:
        return {"siren": siren, "found": False, "retrieved_at": now}
    nj = str(hit.get("nature_juridique") or "")
    siege = hit.get("siege") or {}
    return {
        "siren": siren,
        "found": True,
        "nom_complet": hit.get("nom_complet"),
        "categorie_entreprise": hit.get("categorie_entreprise"),
        "tranche_effectif": hit.get("tranche_effectif_salarie"),
        "nature_juridique": nj or None,
        # Catégorie juridique INSEE 1000 = entrepreneur individuel (personne physique).
        "est_entrepreneur_individuel": nj == "1000"
        or bool((hit.get("complements") or {}).get("est_entrepreneur_individuel")),
        "activite_principale": hit.get("activite_principale"),
        "region_siege": siege.get("region"),
        "etat_administratif": hit.get("etat_administratif"),
        "date_creation": hit.get("date_creation"),
        "retrieved_at": now,
    }


def _fetch(siren: str) -> dict:
    _throttle()
    payload = get_json(config.SIRENE_API, {"q": siren, "page": 1, "per_page": 1})
    return parse_result(siren, payload)


def load_cache() -> dict[str, dict]:
    if not CACHE_FILE.exists():
        return {}
    out = {}
    for line in CACHE_FILE.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["siren"]] = rec
    return out


def candidates(limit: int) -> list[str]:
    """SIREN des titulaires (SIRET valide) les plus importants en montant attribué depuis 2021."""
    con = duckdb.connect(str(config.WAREHOUSE), read_only=True)
    rows = con.sql(f"""
        select titulaire_siren
        from main.int_attributions
        where titulaire_siren is not null
        group by 1
        order by sum(coalesce(montant_part, 0)) desc
        limit {int(limit)}
    """).fetchall()
    con.close()
    return [r[0] for r in rows]


def write_parquet(cache: dict[str, dict]) -> None:
    rows = [r for r in cache.values() if r.get("found")]
    df = pd.DataFrame(rows, columns=COLUMNS) if rows else pd.DataFrame(columns=COLUMNS)
    df["est_entrepreneur_individuel"] = df["est_entrepreneur_individuel"].astype("boolean")
    df.to_parquet(OUT, index=False)
    # Copie versionnée : pour les entrepreneurs individuels (personnes physiques), seuls le SIREN et
    # l'indicateur sont conservés, jamais le nom.
    pub = df.copy()
    ei = pub["est_entrepreneur_individuel"].fillna(False).astype(bool)
    pub.loc[ei, ["nom_complet", "activite_principale", "region_siege", "date_creation"]] = None
    pub.to_parquet(config.DATA / "history" / "sirene_titulaires.parquet", index=False, compression="zstd")
    print(f"{len(rows)} unités SIRENE écrites dans {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=3000)
    ap.add_argument("--init-only", action="store_true", help="écrit le parquet depuis le cache sans appeler l'API")
    args = ap.parse_args()
    cache = load_cache()
    if not args.init_only:
        todo = [s for s in candidates(args.max) if s not in cache]
        print(f"{len(cache)} SIREN en cache, {len(todo)} à interroger")
        with ThreadPoolExecutor(max_workers=4) as pool, open(CACHE_FILE, "a") as f:
            for i, rec in enumerate(pool.map(_fetch, todo), 1):
                cache[rec["siren"]] = rec
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                if i % 100 == 0:
                    print(f"  {i}/{len(todo)}")
    write_parquet(cache)


if __name__ == "__main__":
    main()
