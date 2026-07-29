"""Téléchargement des sources ouvertes (DECP, CPV, référentiel géographique, BOAMP).

Usage : python -m radar.download [decp|cpv|geo|boamp|all]

Par défaut, la DECP est retéléchargée dans la version figée par data/sources.lock.json ;
RADAR_DECP_LATEST=1 force la dernière version publiée.

Chaque téléchargement est tracé dans data/sources.lock.json (URL, date, taille, empreinte)
pour que les chiffres publiés restent reproductibles.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

from . import config
from .net import download, get_json, sha256


def _lock(key: str, entry: dict) -> None:
    lock = json.loads(config.SOURCES_LOCK.read_text()) if config.SOURCES_LOCK.exists() else {}
    lock[key] = entry
    config.SOURCES_LOCK.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n")


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def fetch_decp() -> Path:
    """DECP consolidées par decp.info (Colmo), publiées sur data.gouv.fr au format Parquet."""
    lock = json.loads(config.SOURCES_LOCK.read_text()) if config.SOURCES_LOCK.exists() else {}
    if "decp" in lock and not os.environ.get("RADAR_DECP_LATEST"):
        # Reproductibilité : on retélécharge exactement la version utilisée pour les chiffres publiés.
        res = {
            "url": lock["decp"]["url"],
            "filesize": lock["decp"]["bytes"],
            "last_modified": lock["decp"]["resource_last_modified"],
        }
    else:
        meta = get_json(f"https://www.data.gouv.fr/api/1/datasets/{config.DECP_DATASET}/")
        res = next(r for r in meta["resources"] if r["title"] == config.DECP_RESOURCE_TITLE)
    dest = config.RAW / "decp.parquet"
    if not dest.exists() or dest.stat().st_size != res.get("filesize"):
        print(f"Téléchargement DECP ({res['filesize'] / 1e6:.0f} Mo) : {res['url']}")
        download(res["url"], dest)
    _lock(
        "decp",
        {
            "dataset": f"https://www.data.gouv.fr/datasets/{config.DECP_DATASET}",
            "url": res["url"],
            "resource_last_modified": res["last_modified"],
            "retrieved_at": _now(),
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
            "license": "Licence Ouverte / Open Licence 2.0 (Etalab)",
        },
    )
    return dest


def fetch_cpv() -> Path:
    """Nomenclature CPV 2008 (vocabulaire principal, libellés FR)."""
    rows: list[dict] = []
    offset = 0
    while True:
        page = get_json(
            f"{config.CPV_API}/records",
            {"select": "code_short,fr", "limit": 100, "offset": offset, "order_by": "code_short"},
        )
        rows += page["results"]
        offset += 100
        if offset >= page["total_count"]:
            break
    dest = config.REFERENCE / "cpv.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code_cpv", "libelle"])
        for r in sorted(rows, key=lambda r: r["code_short"]):
            w.writerow([r["code_short"], r["fr"]])
    _lock(
        "cpv",
        {
            "url": config.CPV_API,
            "retrieved_at": _now(),
            "rows": len(rows),
            "license": "CC BY 4.0 (Communautés européennes, règlement (CE) n° 213/2008)",
        },
    )
    return dest


def fetch_geo() -> Path:
    """Régions et départements (COG INSEE via geo.api.gouv.fr)."""
    regions = {r["code"]: r["nom"] for r in get_json(f"{config.GEO_API}/regions")}
    deps = get_json(f"{config.GEO_API}/departements")
    dest = config.REFERENCE / "geo_departements.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code_departement", "nom_departement", "code_region", "nom_region"])
        for d in sorted(deps, key=lambda d: d["code"]):
            w.writerow([d["code"], d["nom"], d["codeRegion"], regions.get(d["codeRegion"], "")])
    _lock(
        "geo",
        {
            "url": f"{config.GEO_API}/departements",
            "retrieved_at": _now(),
            "rows": len(deps),
            "license": "Licence Ouverte 2.0 (COG INSEE)",
        },
    )
    return dest


def fetch_boamp(snapshot: dt.date | None = None) -> Path:
    """Instantané des avis de marché BOAMP encore ouverts à la date de l'instantané.

    L'API limite l'offset à 10 000 : on pagine donc par mois de parution.
    """
    snapshot = snapshot or dt.date.today()
    where_open = f"nature='APPEL_OFFRE' and datelimitereponse >= date'{snapshot.isoformat()}'"
    months = get_json(
        f"{config.BOAMP_API}/records",
        {
            "where": where_open,
            "group_by": "year(dateparution) as y, month(dateparution) as m",
            "select": "count(*) as n",
            "limit": 200,
        },
    )["results"]
    records: list[dict] = []
    for g in months:
        y, m = int(g["y"]), int(g["m"])
        where = f"{where_open} and year(dateparution)={y} and month(dateparution)={m}"
        offset = 0
        while offset < g["n"]:
            page = get_json(
                f"{config.BOAMP_API}/records", {"where": where, "limit": 100, "offset": offset, "order_by": "idweb"}
            )
            records += page["results"]
            offset += 100
        print(f"  {y}-{m:02d} : {g['n']} avis")
    dest = config.RAW / f"boamp_{snapshot.isoformat()}.json"
    dest.write_text(
        json.dumps(
            {"snapshot_date": snapshot.isoformat(), "retrieved_at": _now(), "records": records}, ensure_ascii=False
        )
    )
    _lock(
        "boamp",
        {
            "url": config.BOAMP_API,
            "snapshot_date": snapshot.isoformat(),
            "retrieved_at": _now(),
            "rows": len(records),
            "filter": where_open,
            "license": "Licence Ouverte 2.0 (DILA, BOAMP)",
        },
    )
    return dest


def main(argv: list[str]) -> None:
    what = argv[1] if len(argv) > 1 else "all"
    steps = {"decp": fetch_decp, "cpv": fetch_cpv, "geo": fetch_geo, "boamp": fetch_boamp}
    for name, fn in steps.items():
        if what in (name, "all"):
            print(f"[{name}] {fn()}")


if __name__ == "__main__":
    main(sys.argv)
