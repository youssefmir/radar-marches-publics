"""Aplatissement de l'instantané BOAMP : une ligne par avis, champs utiles au radar.

Les avis existent sous plusieurs schémas (eForms européen, FNSimple, MAPA, anciens schémas BOAMP).
Plutôt que de coder chaque chemin, on parcourt l'arbre JSON et on applique des règles
par motif de chemin (CPV, montant estimé, lots, critères, durée).

Données personnelles : noms, téléphones et e-mails des contacts ne sont PAS extraits.

Usage : python -m radar.boamp [chemin_instantané.json]
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from . import config

# Avis « ouverts » retenus : date limite après l'instantané ET publiés dans les 12 derniers mois.
# Le filtre de parution écarte des avis manifestement erronés (ex. date limite saisie en 7017).
MAX_AGE_DAYS = 365
RE_CPV = re.compile(r"^\d{8}$")
RE_SIRET = re.compile(r"^\d{14}$")
RE_CODE = re.compile(r"^([a-z]+(-[a-z]+)*|[A-Z]{2,4}|true|false|\d+)$")
RE_PRIX = re.compile(r"(?:prix|co[uû]t|montant)[^0-9%]{0,40}?(\d{1,3}(?:[.,]\d+)?)\s*(?:%|pts|points)", re.I)


def leaves(obj, path: str = ""):
    """Énumère (chemin, valeur) pour toutes les feuilles d'un arbre JSON."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for v in obj:
            yield from leaves(v, path)
    elif obj not in (None, ""):
        yield path, str(obj)


def _find_dicts(obj, key: str):
    """Tous les sous-dictionnaires contenant `key`."""
    if isinstance(obj, dict):
        if key in obj:
            yield obj
        for v in obj.values():
            yield from _find_dicts(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from _find_dicts(v, key)


def eforms_criteres(tree) -> list[tuple[str, str, float | None]]:
    """Critères d'attribution eForms : (type, libellé, pondération) dédoublonnés entre lots."""
    out: dict[tuple[str, str], float | None] = {}
    for c in _find_dicts(tree, "cbc:AwardingCriterionTypeCode"):
        t = c["cbc:AwardingCriterionTypeCode"]
        typ = t.get("#text") if isinstance(t, dict) else str(t)
        desc = c.get("cbc:Description")
        desc = desc.get("#text") if isinstance(desc, dict) else (desc or "")
        weight = None
        for path, val in leaves(c):
            if path.endswith("efbc:ParameterNumeric"):
                weight = _num(val)
                break
        out.setdefault((typ or "", (desc or "")[:120]), weight)
    return [(t, d, w) for (t, d), w in out.items()]


def _num(v: str) -> float | None:
    try:
        x = float(v.replace(" ", "").replace(",", "."))
        return x if x > 0 else None
    except ValueError:
        return None


def parse_donnees(raw: str | None) -> dict:
    """Extrait les champs structurés d'un avis, quel que soit son schéma."""
    try:
        tree = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        tree = {}
    cpv: list[str] = []
    descriptions: list[str] = []
    siret = None
    project_values: list[float] = []
    lot_values: list[float] = []
    lot_ids: set[str] = set()
    criteres: list[str] = []
    durees: list[float] = []
    for path, val in leaves(tree):
        p = path.lower()
        last = p.rsplit("/", 1)[-1]
        if ("cpv" in p or "itemclassificationcode" in p) and RE_CPV.match(val):
            if val not in cpv:
                cpv.append(val)
        elif (
            siret is None
            and RE_SIRET.match(val)
            and ("codeidentificationnational" in p or "code_ident_national" in p or "companyid" in p)
        ):
            siret = val
        elif (
            last in ("description", "objet_complet", "#text")
            and ("description" in p or "objet_complet" in p)
            and "criteri" not in p
            and len(val) > 20
        ) and val not in descriptions:
            descriptions.append(val)
        if (
            "estimatedoverallcontractamount/#text" in p
            or ("estimationvaleur/valeur" in p)
            or p.endswith("/valeur_totale")
        ):
            v = _num(val)
            if v:
                (lot_values if "lot" in p else project_values).append(v)
        if re.search(r"procurementprojectlot/cbc:id/#text$", p) or re.search(r"/lots?/(num|@num)$", p):
            lot_ids.add(val)
        if (
            "criter" in p
            and "awardingcriterion" not in p
            and "tendererqualification" not in p
            and "selection" not in p
            and len(val) > 2
            and not RE_CODE.match(val)
        ) and not val.startswith(("http", "ORG-")):
            criteres.append(val)
        if last in ("dureemois", "duree_mois") or ("durationmeasure/#text" in p and "plannedperiod" in p):
            v = _num(val)
            if v:
                durees.append(v)
    nb_lots = len(lot_ids) or len(
        [1 for path, _ in leaves(tree) if re.search(r"/lots?/lot/description$", path.lower())]
    )
    montant = max(project_values) if project_values else (sum(lot_values) if lot_values else None)
    ef = eforms_criteres(tree)
    prix_ef = None
    if ef:
        criteres = [f"{d or t}" + (f" {w:g} %" if w is not None else "") for t, d, w in ef] + criteres
        poids = [w for t, _, w in ef if t in ("price", "cost") and w is not None]
        prix_ef = sum(poids) if poids else None
    crit_txt = " ; ".join(dict.fromkeys(c for c in criteres if not c.isdigit()))[:1500]
    prix = RE_PRIX.search(crit_txt)
    pp = prix_ef if prix_ef is not None else (float(prix.group(1).replace(",", ".")) if prix else None)
    return {
        "cpv_codes": cpv,
        "cpv_principal": cpv[0] if cpv else None,
        "acheteur_siret": siret,
        "description": " ".join(descriptions)[:3000],
        "montant_estime": montant,
        "nb_lots": max(nb_lots, 1),
        "criteres": crit_txt or None,
        "ponderation_prix": pp if pp is not None and 0 < pp <= 100 else None,
        "duree_mois": max(durees) if durees else None,
    }


def _txt(x: Any) -> str | None:
    """Texte nettoyé : entités HTML décodées (« d&#039;Agglomération »), espaces compactés."""
    if not isinstance(x, str):
        return None
    return " ".join(html.unescape(html.unescape(x)).split()) or None


def _dep(code: Any) -> str:
    """Code département sur 2 caractères au minimum (« 2 » -> « 02 »), « 2A »/« 971 » inchangés."""
    c = str(code).strip().upper()
    return c.zfill(2) if c.isdigit() and len(c) < 2 else c


def flatten(snapshot_path: Path) -> pd.DataFrame:
    snap = json.loads(snapshot_path.read_text())
    snapshot_date = dt.date.fromisoformat(snap["snapshot_date"])
    rows = []
    for r in snap["records"]:
        d = parse_donnees(r.get("donnees"))
        deps = [_dep(x) for x in (r.get("code_departement") or [])]
        rows.append(
            {
                "idweb": r["idweb"],
                "url_avis": r.get("url_avis"),
                "objet": (r.get("objet") or "").strip(),
                "acheteur_nom": r.get("nomacheteur"),
                "departements": [str(x) for x in deps],
                "departement_principal": str(deps[0]) if deps else None,
                "date_parution": r.get("dateparution"),
                "date_limite": r.get("datelimitereponse"),
                "famille": r.get("famille"),
                "famille_libelle": r.get("famille_libelle"),
                "procedure": r.get("procedure_libelle"),
                "type_procedure": r.get("type_procedure"),
                "nature": r.get("nature_categorise_libelle"),
                "etat": r.get("etat"),
                "type_marche": (r.get("type_marche") or [None])[0],
                "descripteurs": r.get("descripteur_libelle") or [],
                "criteres_boamp": r.get("criteres") or [],
                "schema": r.get("source_schema"),
                **d,
            }
        )
    df = pd.DataFrame(rows)
    df["snapshot_date"] = snapshot_date.isoformat()
    parution = pd.to_datetime(df["date_parution"], errors="coerce")
    limite = pd.to_datetime(df["date_limite"], errors="coerce", utc=True).dt.tz_localize(None)
    df["exclu_motif"] = None
    df.loc[parution < pd.Timestamp(snapshot_date - dt.timedelta(days=MAX_AGE_DAYS)), "exclu_motif"] = (
        "parution_ancienne"
    )
    df.loc[limite > pd.Timestamp(snapshot_date + dt.timedelta(days=730)), "exclu_motif"] = "date_limite_improbable"
    df.loc[df["etat"] == "ANNULATION", "exclu_motif"] = "avis_annule"
    return df


def latest_snapshot() -> Path:
    files = sorted(config.RAW.glob("boamp_*.json"))
    if not files:
        raise SystemExit("Aucun instantané BOAMP : lancez `python -m radar.download boamp`.")
    return files[-1]


def main(argv: list[str]) -> None:
    src = Path(argv[1]) if len(argv) > 1 else latest_snapshot()
    df = flatten(src)
    out_all = config.INTERIM / "boamp_avis.parquet"
    df.to_parquet(out_all, index=False)
    # Copie versionnée (compacte, sans données personnelles) pour la reproductibilité de la démo.
    df.to_parquet(
        config.SNAPSHOTS / f"boamp_avis_{df['snapshot_date'].iat[0]}.parquet", index=False, compression="zstd"
    )
    print(f"{len(df)} avis, dont {df['exclu_motif'].isna().sum()} retenus ; exclusions :")
    print(df["exclu_motif"].value_counts().to_string())


if __name__ == "__main__":
    main(sys.argv)
