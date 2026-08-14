"""Score hybride expliqué du Radar AO et grille go/no-go.

Chaque composante est ramenée dans [0, 1] puis pondérée (config/profils.yml, clé `poids`).
Le résultat expose la décomposition complète : aucune « boîte noire ».
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
import yaml

from . import config
from .history import HISTORY
from .index import AvisIndex, minmax
from .text import strip_accents

COMPOSANTES = {
    "semantique": "Proximité de sens entre le profil et l'avis (embeddings multilingues)",
    "lexical": "Mots-clés communs (BM25)",
    "cpv": "Adéquation des codes CPV (même code, classe, groupe ou division)",
    "geographie": "Lieu d'exécution dans les départements ciblés (ou la même région)",
    "taille": "Montant estimé dans la fourchette visée",
    "concurrence": "Intensité concurrentielle historique (DECP) : moins d'offres = meilleure chance",
    "sortant": "Absence de titulaire sortant dominant chez cet acheteur pour ce type d'achat",
}


@dataclass
class Profil:
    nom: str
    description: str
    cpv: list[str] = field(default_factory=list)
    departements: list[str] = field(default_factory=list)
    montant_min: float | None = None
    montant_max: float | None = None
    id: str = "personnalise"
    fictif: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Profil:
        keys = {"nom", "description", "cpv", "departements", "montant_min", "montant_max", "id", "fictif"}
        return cls(**{k: v for k, v in d.items() if k in keys}, extra={k: v for k, v in d.items() if k not in keys})


def load_config() -> dict[str, Any]:
    return yaml.safe_load((config.ROOT / "config" / "profils.yml").read_text())


@lru_cache(maxsize=1)
def regions() -> dict[str, str]:
    with open(config.REFERENCE / "geo_departements.csv", encoding="utf-8") as f:
        return {r["code_departement"]: r["code_region"] for r in csv.DictReader(f)}


@lru_cache(maxsize=1)
def cpv_labels() -> dict[str, str]:
    with open(config.REFERENCE / "cpv.csv", encoding="utf-8") as f:
        return {r["code_cpv"]: r["libelle"] for r in csv.DictReader(f)}


# --- Composantes ---------------------------------------------------------------------------


def cpv_match(profil_codes: list[str], avis_codes: list[str]) -> float:
    """1 même code ; 0,8 même classe (4 chiffres) ; 0,6 même groupe (3) ; 0,3 même division (2) ; 0 sinon."""
    best = 0.0
    for p in profil_codes:
        for a in avis_codes:
            if p == a:
                return 1.0
            for n, s in ((4, 0.8), (3, 0.6), (2, 0.3)):
                if p[:n] == a[:n]:
                    best = max(best, s)
                    break
    return best


def geo_match(profil_deps: list[str], avis_deps: list[str]) -> float:
    if not profil_deps:
        return 1.0
    if not avis_deps:
        return 0.3  # lieu non renseigné : neutre-prudent
    if set(profil_deps) & set(avis_deps):
        return 1.0
    reg = regions()
    if {reg.get(d) for d in profil_deps} & {reg.get(d) for d in avis_deps} - {None}:
        return 0.6
    return 0.0


def taille_match(montant: float | None, lo: float | None, hi: float | None) -> float:
    if montant is None or (isinstance(montant, float) and math.isnan(montant)) or (lo is None and hi is None):
        return 0.5  # montant non publié : neutre
    lo = lo or 0
    hi = hi or float("inf")
    if lo <= montant <= hi:
        return 1.0
    bound = lo if montant < lo else hi
    return float(math.exp(-2 * abs(math.log10(max(montant, 1) / max(bound, 1)))))


def concurrence_score(offres_moyennes: float | None) -> float:
    """5 offres en moyenne ≈ 0,5 ; 1 offre ≈ 0,9 ; 15 offres ≈ 0,1 (décroissance logistique)."""
    if offres_moyennes is None or (isinstance(offres_moyennes, float) and math.isnan(offres_moyennes)):
        return 0.5
    return float(1 / (1 + math.exp(0.45 * (offres_moyennes - 5))))


def sortant_score(part: float | None, nb_marches: int | None) -> float:
    """Pénalise un acheteur où un même titulaire détient l'essentiel des marchés comparables."""
    if part is None or nb_marches is None or (isinstance(part, float) and math.isnan(part)) or nb_marches < 3:
        return 0.7
    return float(1 - 0.8 * part)


# --- Historique -----------------------------------------------------------------------------


@lru_cache(maxsize=1)
def history() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ach = pd.read_parquet(HISTORY / "acheteurs.parquet")
    conc = pd.read_parquet(HISTORY / "concurrence_acheteur_cpv.parquet").set_index(["acheteur_id", "groupe_cpv"])
    dep = pd.read_parquet(HISTORY / "concurrence_dep_cpv.parquet").set_index(["departement_code", "groupe_cpv"])
    return ach, conc, dep


def _norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents((s or "").lower())).strip()


@lru_cache(maxsize=1)
def _acheteur_lookup() -> tuple[set[str], dict[str, str]]:
    ach, _, _ = history()
    sirets = set(ach["acheteur_id"])
    by_name = (
        ach.sort_values("nb_marches", ascending=False)
        .drop_duplicates("nom_normalise")
        .set_index("nom_normalise")["acheteur_id"]
        .to_dict()
    )
    return sirets, by_name


def match_acheteur(siret: str | None, nom: str | None) -> tuple[str | None, str]:
    sirets, by_name = _acheteur_lookup()
    siret = siret if isinstance(siret, str) else None
    if siret and siret in sirets:
        return siret, "siret"
    n = _norm(nom if isinstance(nom, str) else None)
    if n and n in by_name:
        return by_name[n], "nom"
    return None, "aucun"


def historique_avis(row: pd.Series) -> dict[str, Any]:
    """Statistiques DECP pour l'acheteur de l'avis et le groupe CPV principal (repli département)."""
    _, conc, dep = history()
    acheteur_id, mode = match_acheteur(_s(row.get("acheteur_siret")), _s(row.get("acheteur_nom")))
    groupe = (_s(row.get("cpv_principal")) or "")[:3]
    out: dict[str, Any] = {
        "acheteur_id": acheteur_id,
        "rapprochement": mode,
        "groupe_cpv": groupe or None,
        "niveau": None,
    }
    if acheteur_id and groupe and (acheteur_id, groupe) in conc.index:
        h = conc.loc[(acheteur_id, groupe)]
        out.update(
            niveau="acheteur",
            nb_marches=int(h["nb_marches"]),
            nb_marches_offres=int(h["nb_marches_offres"]),
            offres_moyennes=_f(h["offres_moyennes"]),
            taux_offre_unique=_f(h["taux_offre_unique"]),
            montant_median=_f(h["montant_median"]),
            titulaire_principal=h["titulaire_principal_nom"],
            titulaire_principal_categorie=h["titulaire_principal_categorie"],
            titulaire_principal_part=_f(h["titulaire_principal_part"]),
            derniere_attribution=str(h["derniere_attribution"])[:10],
        )
        if out["nb_marches_offres"] >= 3:
            return out
    d = _s(row.get("departement_principal"))
    if d and groupe and (d, groupe) in dep.index:
        h = dep.loc[(d, groupe)]
        out.setdefault("nb_marches", None)
        out.update(
            niveau_concurrence="departement",
            offres_moyennes=_f(h["offres_moyennes"]),
            taux_offre_unique=_f(h["taux_offre_unique"]),
            nb_marches_departement=int(h["nb_marches"]),
        )
        out["niveau"] = out["niveau"] or "departement"
    return out


def _s(x: Any) -> str | None:
    return x if isinstance(x, str) and x else None


def _f(x: Any) -> float | None:
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


# --- Go / no-go -----------------------------------------------------------------------------


def go_no_go(row: pd.Series, profil: Profil, today: dt.date) -> list[dict[str, str]]:
    """Grille de qualification à partir des seuls champs structurés de l'avis."""
    items: list[dict[str, str]] = []
    lim = pd.to_datetime(row.get("date_limite"), errors="coerce", utc=True)
    if pd.isna(lim):
        items.append({"critere": "Date limite", "statut": "inconnu", "detail": "Non renseignée"})
    else:
        jours = (lim.date() - today).days
        st = "ok" if jours >= 15 else ("attention" if jours >= 7 else "risque")
        items.append(
            {
                "critere": "Date limite",
                "statut": st,
                "detail": f"{lim.date().strftime('%d/%m/%Y')} — {jours} jour(s) pour répondre",
            }
        )
    proc = (_s(row.get("procedure")) or "").strip()
    tp = (_s(row.get("type_procedure")) or "").upper()
    if "RESTREINT" in tp or "restreint" in proc.lower() or "NEGOCI" in tp:
        items.append(
            {
                "critere": "Procédure",
                "statut": "attention",
                "detail": f"{proc or tp} : candidature puis sélection avant l'offre",
            }
        )
    elif proc or tp:
        items.append({"critere": "Procédure", "statut": "ok", "detail": proc or tp})
    else:
        items.append({"critere": "Procédure", "statut": "inconnu", "detail": "Non renseignée"})
    nb_lots = int(row.get("nb_lots") or 1)
    items.append(
        {
            "critere": "Allotissement",
            "statut": "ok" if nb_lots > 1 else "info",
            "detail": f"{nb_lots} lots : possibilité de cibler un lot" if nb_lots > 1 else "Lot unique",
        }
    )
    m = _f(row.get("montant_estime"))
    if m is None:
        items.append({"critere": "Montant estimé", "statut": "inconnu", "detail": "Non publié dans l'avis"})
    else:
        ok = (profil.montant_min or 0) <= m <= (profil.montant_max or float("inf"))
        items.append(
            {
                "critere": "Montant estimé",
                "statut": "ok" if ok else "attention",
                "detail": f"{m:,.0f} € HT".replace(",", " ") + ("" if ok else " (hors fourchette visée)"),
            }
        )
    p = _f(row.get("ponderation_prix"))
    if p is not None:
        st = "attention" if p >= 60 else "ok"
        items.append(
            {
                "critere": "Poids du prix",
                "statut": st,
                "detail": f"{p:g} % — " + ("guerre des prix probable" if p >= 60 else "valeur technique déterminante"),
            }
        )
    elif _s(row.get("criteres")):
        items.append({"critere": "Critères", "statut": "info", "detail": str(row["criteres"])[:160]})
    else:
        items.append({"critere": "Critères", "statut": "inconnu", "detail": "Non structurés dans l'avis"})
    du = _f(row.get("duree_mois"))
    if du is not None:
        items.append({"critere": "Durée", "statut": "info", "detail": f"{du:g} mois"})
    return items


def verdict(items: list[dict[str, str]]) -> str:
    if any(i["statut"] == "risque" for i in items):
        return "no-go probable"
    n_att = sum(i["statut"] == "attention" for i in items)
    return "go" if n_att == 0 else ("à étudier" if n_att <= 2 else "no-go probable")


# --- Classement -----------------------------------------------------------------------------


def profil_query(profil: Profil) -> str:
    labels = cpv_labels()
    cpv_txt = ", ".join(labels.get(c, "") for c in profil.cpv[:8] if labels.get(c))
    return f"{profil.description} {cpv_txt}".strip()


def rank(
    index: AvisIndex, profil: Profil, poids: dict[str, float] | None = None, top: int = 25, today: dt.date | None = None
) -> list[dict[str, Any]]:
    poids = poids or load_config()["poids"]
    av = index.avis
    today = today or dt.date.fromisoformat(av["snapshot_date"].iat[0])
    q = profil_query(profil)
    comp = pd.DataFrame(
        {
            "semantique": minmax(index.semantic_scores(q)),
            "lexical": minmax(index.lexical_scores(q)),
            "cpv": [cpv_match(profil.cpv, list(c)) for c in av["cpv_codes"]],
            "geographie": [geo_match(profil.departements, list(d)) for d in av["departements"]],
            "taille": [taille_match(_f(m), profil.montant_min, profil.montant_max) for m in av["montant_estime"]],
        }
    )
    # Pré-score sans historique pour limiter le calcul des signaux DECP aux meilleurs candidats.
    pre = sum(comp[k] * poids[k] for k in comp.columns)
    cand = np.argsort(-pre.to_numpy())[: max(top * 8, 200)]
    results = []
    for i in cand:
        row = av.iloc[i]
        h = historique_avis(row)
        c = comp.iloc[i].to_dict()
        c["concurrence"] = concurrence_score(h.get("offres_moyennes"))
        c["sortant"] = sortant_score(h.get("titulaire_principal_part"), h.get("nb_marches"))
        score = sum(c[k] * poids[k] for k in poids)
        results.append((score, i, c, h))
    results.sort(key=lambda r: -r[0])
    out = []
    for score, i, c, h in results[:top]:
        row = av.iloc[i]
        gng = go_no_go(row, profil, today)
        out.append(
            {
                "idweb": row["idweb"],
                "url": row["url_avis"],
                "objet": row["objet"],
                "acheteur": row["acheteur_nom"],
                "departements": list(row["departements"]),
                "date_limite": row["date_limite"],
                "date_parution": row["date_parution"],
                "procedure": row["procedure"],
                "type_marche": row["type_marche"],
                "cpv": [{"code": x, "libelle": cpv_labels().get(x, "")} for x in list(row["cpv_codes"])[:4]],
                "montant_estime": _f(row["montant_estime"]),
                "nb_lots": int(row["nb_lots"]),
                "score": round(100 * score, 1),
                "composantes": {
                    k: {
                        "valeur": round(float(v), 3),
                        "poids": poids[k],
                        "contribution": round(100 * float(v) * poids[k], 1),
                    }
                    for k, v in c.items()
                },
                "historique": h,
                "go_no_go": gng,
                "verdict": verdict(gng),
                "extrait": (_s(row["description"]) or "")[:400],
            }
        )
    return out
