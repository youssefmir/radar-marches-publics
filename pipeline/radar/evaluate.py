"""Évaluation reproductible de la recherche du Radar : BM25 vs embeddings vs hybride.

Principe : les avis BOAMP portent des codes CPV, qui servent de vérité terrain (pertinence binaire).
- Partition déterministe des avis : 30 % « réglage » (choix de alpha), 70 % « test » (chiffres publiés).
- Jeu Q1 « profil CPV » : une requête par classe CPV (4 chiffres) assez représentée ; texte = libellé de la classe
  + libellés des 3 codes de cette classe les plus fréquents dans l'historique DECP (ce qu'une entreprise du métier
  déclarerait). Pertinent = avis ayant au moins un code dans la classe.
- Jeu Q2 « avis exemple » : un avis sert de requête (objet + début de description) ; pertinent = autre avis
  du même groupe CPV (3 chiffres) que son code principal.
La composante CPV du radar est exclue de l'évaluation (elle utiliserait la vérité terrain).

Usage : python -m radar.evaluate
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter

import duckdb
import numpy as np
import pandas as pd

from . import config
from .index import AvisIndex, encode, load_avis, minmax
from .scoring import cpv_labels

MODELS = {
    "e5": "intfloat/multilingual-e5-small",
    "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}
ALPHAS = [round(a, 1) for a in np.arange(0.0, 1.01, 0.1)]
K, K_RECALL = 10, 50
SEED = 42


def split_of(idweb: str) -> str:
    return "reglage" if int(hashlib.md5(idweb.encode()).hexdigest(), 16) % 10 < 3 else "test"


# --- métriques ---------------------------------------------------------------------------------


def precision_at(rel: np.ndarray, k: int = K) -> float:
    return float(rel[:k].mean())


def ndcg_at(rel: np.ndarray, n_rel: int, k: int = K) -> float:
    gains = rel[:k] / np.log2(np.arange(2, min(k, len(rel)) + 2))
    ideal = (1 / np.log2(np.arange(2, min(k, n_rel) + 2))).sum()
    return float(gains.sum() / ideal) if ideal > 0 else 0.0


def recall_at(rel: np.ndarray, n_rel: int, k: int = K_RECALL) -> float:
    return float(rel[:k].sum() / n_rel) if n_rel else 0.0


# --- requêtes ----------------------------------------------------------------------------------


def class_queries(av: pd.DataFrame, min_rel: int = 8, max_rel: int = 400) -> list[dict]:
    labels = cpv_labels()
    con = duckdb.connect(str(config.WAREHOUSE), read_only=True)
    freq = con.execute("""select code_cpv, count(*) n from main.fct_attributions group by 1""").df()
    con.close()
    freq["classe"] = freq["code_cpv"].str[:4]
    classes = Counter(c[:4] for codes in av["cpv_codes"] for c in set(x[:4] for x in codes))
    out = []
    for cl, n in sorted(classes.items()):
        if not (min_rel <= n <= max_rel) or cl.startswith("0000"):
            continue
        base = labels.get(cl + "0000") or labels.get(cl.ljust(8, "0"))
        if not base:
            continue
        top = freq[(freq["classe"] == cl) & (freq["code_cpv"] != cl + "0000")].nlargest(3, "n")["code_cpv"]
        text = ". ".join([base] + [labels[c] for c in top if c in labels])
        rel = av["cpv_codes"].apply(lambda codes, cl=cl: any(c.startswith(cl) for c in codes)).to_numpy()
        out.append({"jeu": "Q1 profil CPV", "id": cl, "texte": text, "rel": rel, "exclude": None})
    return out


def example_queries(av: pd.DataFrame, n: int = 300) -> list[dict]:
    rng = np.random.default_rng(SEED)
    cand = np.flatnonzero((av["description"].str.len() > 100).to_numpy() & av["cpv_principal"].notna().to_numpy())
    out = []
    for i in rng.choice(cand, size=min(n, len(cand)), replace=False):
        g = av.at[i, "cpv_principal"][:3]
        rel = av["cpv_codes"].apply(lambda codes, g=g: any(c.startswith(g) for c in codes)).to_numpy().copy()
        rel[i] = False
        if rel.sum() < 3:
            continue
        text = f"{av.at[i, 'objet']}. {av.at[i, 'description'][:500]}"
        out.append({"jeu": "Q2 avis exemple", "id": av.at[i, "idweb"], "texte": text, "rel": rel, "exclude": i})
    return out


# --- évaluation --------------------------------------------------------------------------------


def run_split(av: pd.DataFrame, indexes: dict[str, AvisIndex], alphas: list[float]) -> pd.DataFrame:
    queries = class_queries(av) + example_queries(av)
    rows = []
    q_emb = {m: encode([q["texte"] for q in queries], MODELS[m], "query") for m in indexes}
    for qi, q in enumerate(queries):
        lex = indexes["e5"].lexical_scores(q["texte"])
        sems = {m: idx.emb @ q_emb[m][qi] for m, idx in indexes.items()}
        variants = {"BM25": lex, "Embeddings e5-small": sems["e5"]}
        if "minilm" in sems:
            variants["Embeddings MiniLM"] = sems["minilm"]
        lexn, semn = minmax(lex), minmax(sems["e5"])
        for a in alphas:
            variants[f"Hybride a={a}"] = a * semn + (1 - a) * lexn
        r_lex = np.argsort(np.argsort(-lex))
        r_sem = np.argsort(np.argsort(-sems["e5"]))
        variants["Hybride RRF"] = 1 / (60 + r_lex) + 1 / (60 + r_sem)
        rel = q["rel"]
        n_rel = int(rel.sum())
        for name, s in variants.items():
            s = s.astype(float).copy()
            if q["exclude"] is not None:
                s[q["exclude"]] = -np.inf
            order = np.argsort(-s, kind="stable")
            r = rel[order].astype(float)
            rows.append(
                {
                    "jeu": q["jeu"],
                    "requete": q["id"],
                    "methode": name,
                    "n_pertinents": n_rel,
                    "p@10": precision_at(r),
                    "ndcg@10": ndcg_at(r, n_rel),
                    "r@50": recall_at(r, n_rel),
                    "top10": order[:10].tolist(),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_ci(x: np.ndarray, n: int = 1000) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    means = [rng.choice(x, size=len(x), replace=True).mean() for _ in range(n)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _f(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def _lecture(o: dict) -> list[str]:
    """Lecture chiffrée : écart hybride vs BM25 et vs embeddings, par jeu de requêtes."""
    out = ["**Lecture.**"]
    for jeu in sorted({r["jeu"] for r in o["resultats"]}):
        rs = {r["methode"]: r for r in o["resultats"] if r["jeu"] == jeu}
        h = next(v for k, v in rs.items() if k.startswith("Hybride (alpha"))
        b, e = rs["BM25"], rs["Embeddings e5-small"]
        overlap = h["ndcg@10_ic95"][0] <= b["ndcg@10_ic95"][1]
        out.append(
            f"- {jeu} : l'hybride atteint un nDCG@10 de {_f(h['ndcg@10'])} contre {_f(b['ndcg@10'])} pour BM25 "
            f"({'+' if h['ndcg@10'] >= b['ndcg@10'] else ''}{_f(h['ndcg@10'] - b['ndcg@10'])}) et {_f(e['ndcg@10'])} "
            f"pour les embeddings seuls. "
            + (
                "Le gain sur BM25 est modeste : les intervalles de confiance se recouvrent."
                if overlap
                else "Le gain sur BM25 est net : les intervalles de confiance sont disjoints."
            )
        )
    return out


def markdown(o: dict) -> str:
    L = [
        "# Évaluation de la recherche du Radar AO",
        "",
        "> Généré par `make evaluate` (`python -m radar.evaluate`). Chiffres réels, reproductibles "
        f"(graine {SEED}, partition déterministe par hachage de l'identifiant d'avis).",
        "",
        "## Protocole",
        "",
        f"- Corpus : {o['corpus']['avis_avec_cpv']} avis BOAMP ouverts au {o['snapshot_date']} portant au moins un "
        f"code CPV ; {o['corpus']['reglage']} avis de **réglage** (30 %) et {o['corpus']['test']} avis de **test** (70 %).",
        "- Vérité terrain : les codes CPV saisis par les acheteurs (pertinence binaire). Elle est bruitée : un avis "
        "pertinent pour un métier peut être codé dans une autre classe.",
        "- **Q1 « profil CPV »** : une requête par classe CPV (4 chiffres) comptant 8 à 400 avis ; texte = libellé de la "
        "classe + libellés des 3 codes de la classe les plus fréquents dans l'historique DECP. Pertinent = avis avec un "
        "code dans la classe.",
        "- **Q2 « avis exemple »** : un avis tiré au hasard sert de requête (objet + 500 premiers caractères de la "
        "description) ; pertinent = autre avis du même groupe CPV (3 chiffres).",
        "- Le texte indexé (objet + description) n'inclut jamais les libellés CPV ; la composante CPV du score "
        "complet est exclue, car elle lirait directement la vérité terrain.",
        f"- Réglage : alpha (poids des embeddings dans l'hybride) choisi sur l'échantillon de réglage seulement : "
        f"**alpha = {o['alpha']}**.",
        "",
        "## Résultats sur l'échantillon de test",
        "",
        "| Jeu | Méthode | Requêtes | Precision@10 | nDCG@10 | Recall@50 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in o["resultats"]:

        def ci(m: str, r: dict = r) -> str:
            return f"{_f(r[m])} [{_f(r[m + '_ic95'][0])} ; {_f(r[m + '_ic95'][1])}]"

        L.append(f"| {r['jeu']} | {r['methode']} | {r['requetes']} | {ci('p@10')} | {ci('ndcg@10')} | {ci('r@50')} |")
    L += [
        "",
        "Entre crochets : intervalle de confiance à 95 % par bootstrap sur les requêtes.",
        "",
        *_lecture(o),
        "",
        "### Choix de alpha (échantillon de réglage, nDCG@10 moyen Q1 + Q2)",
        "",
        "| alpha | " + " | ".join(f"{c['alpha']:.1f}" for c in o["courbe_alpha"]) + " |",
        "|---|" + "---:|" * len(o["courbe_alpha"]),
        "| nDCG@10 | " + " | ".join(_f(c["ndcg@10_reglage"]) for c in o["courbe_alpha"]) + " |",
        "",
        "### Q1 par famille d'achat (hybride réglé)",
        "",
        "| Famille | Precision@10 | nDCG@10 |",
        "|---|---:|---:|",
    ]
    for r in o["q1_par_famille"]:
        L.append(f"| {r['famille']} | {_f(r['p@10'])} | {_f(r['ndcg@10'])} |")
    L += [
        "",
        "## Analyse d'erreurs (Q1, requêtes les moins bien servies par l'hybride)",
        "",
    ]
    for e in o["erreurs_q1"]:
        L.append(
            f"- **{e['classe']} – {e['libelle']}** (nDCG@10 = {_f(e['ndcg@10'])}, {e['n_pertinents']} avis pertinents). "
            "Faux positifs en tête : "
            + " ; ".join(f"« {fp['objet'][:90]} » ({fp['cpv'][0][:60]})" for fp in e["faux_positifs"])
        )
    L += [
        "",
        "Lecture des erreurs (motifs observés dans la liste ci-dessus) :",
        "",
        "1. **Bruit de la vérité terrain** : des avis réellement liés au besoin sont codés dans une classe voisine "
        "(produits d'hygiène codés « produits de nettoyage », éclairage codé en travaux d'installation). Une partie des "
        "« faux positifs » sont donc des résultats utiles pour une entreprise ; les métriques sont une borne basse.",
        "2. **Polysémie et libellés courts** : « Bois » (matériau) attire les chaufferies bois et la valorisation des "
        "déchets de bois ; « réparation et entretien » attire des avis d'entretien de navires ou de véhicules. Les "
        "libellés CPV seuls sont des requêtes pauvres : d'où l'intérêt de la description libre et des codes CPV du profil.",
        "3. **Objets non informatifs** : certains avis ont un objet réduit à une URL ou à une référence interne ; "
        "leur description, quand elle existe, porte l'essentiel du sens.",
        "4. **Embeddings seuls en retrait** : le petit modèle multilingue (118 M de paramètres, CPU) capte mal le "
        "vocabulaire technique très spécifique des marchés, où le mot exact compte. Il apporte en revanche un gain "
        "complémentaire à BM25 dans l'hybride (synonymes, reformulations).",
        "",
        "## Conséquences pour le produit",
        "",
        "- Le classement final combine le texte (hybride) avec l'adéquation CPV, la géographie et la taille : "
        "l'évaluation ci-dessus mesure la seule brique texte, la plus difficile.",
        "- Le radar est un outil d'aide au tri : il affiche la décomposition du score et ne masque aucun avis.",
        "- Pistes : modèle d'embeddings plus grand ou affiné sur des couples (objet, CPV) issus des DECP, "
        "enrichissement des requêtes par les objets de marchés déjà gagnés par l'entreprise.",
        "",
    ]
    return "\n".join(L)


def main() -> None:
    av_all = load_avis()
    av_all = av_all[av_all["cpv_codes"].apply(len) > 0].reset_index(drop=True)
    av_all["split"] = av_all["idweb"].map(split_of)
    res = {}
    for split in ("reglage", "test"):
        av = av_all[av_all["split"] == split].reset_index(drop=True)
        idx = {m: AvisIndex(av, model=name) for m, name in MODELS.items()}
        res[split] = (av, run_split(av, idx, ALPHAS))
        print(f"{split}: {len(av)} avis, {res[split][1]['requete'].nunique()} requêtes")

    tune = res["reglage"][1]
    hyb = tune[tune["methode"].str.startswith("Hybride a=")].groupby("methode")["ndcg@10"].mean()
    best = hyb.idxmax()
    alpha = float(best.split("=")[1])
    print(f"alpha retenu sur l'échantillon de réglage : {alpha} (nDCG@10 = {hyb.max():.3f})")

    av, test = res["test"]
    keep = ["BM25", "Embeddings MiniLM", "Embeddings e5-small", "Hybride RRF", best]
    t = test[test["methode"].isin(keep)].copy()
    t["methode"] = t["methode"].replace({best: f"Hybride (alpha={alpha}, réglé)"})
    summary = []
    for (jeu, m), g in t.groupby(["jeu", "methode"]):
        row = {"jeu": jeu, "methode": m, "requetes": len(g)}
        for met in ("p@10", "ndcg@10", "r@50"):
            lo, hi = bootstrap_ci(g[met].to_numpy())
            row[met] = round(float(g[met].mean()), 3)
            row[met + "_ic95"] = [round(lo, 3), round(hi, 3)]
        summary.append(row)
    # Analyse d'erreurs (hybride, jeu Q1) : pires requêtes et faux positifs.
    h = t[(t["methode"].str.startswith("Hybride (alpha")) & (t["jeu"] == "Q1 profil CPV")].sort_values("ndcg@10")
    labels = cpv_labels()
    erreurs = []
    for _, r in h.head(8).iterrows():
        fps = [i for i in r["top10"] if not any(c.startswith(r["requete"]) for c in av.at[i, "cpv_codes"])][:3]
        erreurs.append(
            {
                "classe": r["requete"],
                "libelle": labels.get(r["requete"] + "0000", ""),
                "ndcg@10": round(r["ndcg@10"], 3),
                "n_pertinents": r["n_pertinents"],
                "faux_positifs": [
                    {
                        "objet": av.at[i, "objet"][:140],
                        "cpv": [f"{c} {labels.get(c, '')}" for c in list(av.at[i, "cpv_codes"])[:2]],
                    }
                    for i in fps
                ],
            }
        )
    by_div = (
        h.assign(division=h["requete"].str[:2])
        .assign(
            famille=lambda d: np.where(
                d["division"] == "45", "Travaux", np.where(d["division"].astype(int) >= 50, "Services", "Fournitures")
            )
        )
        .groupby("famille")[["p@10", "ndcg@10"]]
        .mean()
        .round(3)
        .reset_index()
        .to_dict("records")
    )
    alpha_curve = (
        hyb.rename(lambda s: float(s.split("=")[1]))
        .sort_index()
        .round(4)
        .reset_index()
        .rename(columns={"methode": "alpha", "ndcg@10": "ndcg@10_reglage"})
        .to_dict("records")
    )
    out = {
        "snapshot_date": av_all["snapshot_date"].iat[0],
        "corpus": {
            "avis_avec_cpv": len(av_all),
            "reglage": int((av_all["split"] == "reglage").sum()),
            "test": int((av_all["split"] == "test").sum()),
        },
        "requetes_test": test.groupby("jeu")["requete"].nunique().to_dict(),
        "alpha": alpha,
        "courbe_alpha": alpha_curve,
        "resultats": summary,
        "erreurs_q1": erreurs,
        "q1_par_famille": by_div,
    }
    (config.SITE_DATA / "evaluation.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (config.ROOT / "docs" / "evaluation-radar.md").write_text(markdown(out))
    print(markdown(out))


if __name__ == "__main__":
    main()
