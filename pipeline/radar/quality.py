"""Rapport de qualité des données DECP : complétude, aberrations, doublons, impact des règles.

Produit docs/qualite-donnees.md et web/public/data/qualite.json.
Usage : python -m radar.quality
"""

from __future__ import annotations

import json
from typing import Any

import duckdb

from . import config

RAW = f"read_parquet('{config.RAW / 'decp.parquet'}')"


def _one(con: duckdb.DuckDBPyConnection, sql: str) -> Any:
    return con.execute(sql).fetchone()[0]


def compute(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    q: dict[str, Any] = {}
    q["source"] = json.loads(config.SOURCES_LOCK.read_text())["decp"]
    q["lignes_source"] = _one(con, f"select count(*) from {RAW}")
    q["lignes_attribution_initiale"] = _one(con, "select count(*) from main.stg_decp__attributions")
    q["date_max_notification"] = str(_one(con, "select max(date_notification) from main.int_attributions"))

    # Entonnoir des règles (lignes marché × titulaire)
    hors_periode = _one(con, """select count(*) from main.stg_decp__attributions
        where date_notification is null or date_notification < date '2021-01-01' or date_notification > current_date""")
    sans_acheteur = _one(con, """select count(*) from main.stg_decp__attributions
        where date_notification between date '2021-01-01' and current_date and acheteur_id is null""")
    perimetre = q["lignes_attribution_initiale"] - hors_periode - sans_acheteur
    apres_r2 = _one(con, """select count(*) from (select distinct marche_uid, coalesce(titulaire_id, '?')
        from main.stg_decp__attributions
        where date_notification between date '2021-01-01' and current_date and acheteur_id is not null)""")
    final = _one(con, "select count(*) from main.int_attributions")
    uids_source = _one(con, "select count(distinct marche_uid_source) from main.int_attributions")
    marches = _one(con, "select count(distinct marche_uid) from main.int_attributions")
    q["entonnoir"] = [
        {"etape": "Attributions initiales publiées (toutes dates)", "lignes": q["lignes_attribution_initiale"]},
        {"etape": "R1 – hors période 2021→aujourd'hui ou date absente", "lignes": -hors_periode},
        {"etape": "R1b – acheteur non identifié", "lignes": -sans_acheteur},
        {"etape": "Périmètre analysé", "lignes": perimetre, "total": True},
        {"etape": "R2 – doublons exacts (même marché, même titulaire)", "lignes": apres_r2 - perimetre},
        {"etape": "R2b – quasi-doublons (même acheteur, objet, montant, date, titulaire)", "lignes": final - apres_r2},
        {"etape": "Attributions retenues (fct_attributions)", "lignes": final, "total": True},
    ]
    q["marches"] = {"identifiants_source": uids_source, "marches_apres_r2c": marches,
                    "fusionnes_r2c": uids_source - marches}

    def dist(col: str, amount: bool = False) -> list[dict]:
        extra = ", sum(montant_declare) filter (where montant_declare < 1e10) as montant" if amount else ""
        rows = con.execute(f"select {col} as statut, count(*) as n {extra} from main.int_attributions group by 1 order by 2 desc").df()
        rows["part"] = rows["n"] / final
        return rows.to_dict("records")

    q["montant_statut"] = dist("montant_statut", amount=True)
    q["offres_statut"] = dist("offres_statut")
    q["montant_suspect"] = con.execute("""select count(*) as n, sum(montant_part) as montant,
        sum(montant_part) / (select sum(montant_part) from main.int_attributions) as part_montant
        from main.int_attributions where montant_anomalie = 'suspect'""").df().to_dict("records")[0]
    q["siret"] = con.execute("""select
        avg(case when acheteur_siret_valide then 1.0 else 0 end) as acheteur_valide,
        avg(case when titulaire_type_id = 'SIRET' then 1.0 else 0 end) as titulaire_type_siret,
        avg(case when titulaire_siret_valide then 1.0 else 0 end) as titulaire_siret_valide,
        count(*) filter (where titulaire_type_id = 'SIRET' and not titulaire_siret_valide) as titulaire_siret_invalides
        from main.int_attributions""").df().to_dict("records")[0]
    comp = con.execute("""select
        avg((code_cpv is not null)::int) as code_cpv,
        avg((code_cpv in (select code_cpv from main.dim_cpv))::int) as code_cpv_dans_nomenclature,
        avg((procedure_code <> 'NR')::int) as procedure,
        avg((montant_statut = 'ok')::int) as montant_exploitable,
        avg((offres_statut = 'ok')::int) as offres_exploitables,
        avg((titulaire_categorie <> 'Inconnue')::int) as categorie_titulaire,
        avg((objet is not null and length(objet) > 5)::int) as objet,
        avg((duree_mois is not null)::int) as duree_mois,
        avg((acheteur_departement_code is not null)::int) as departement_acheteur
        from main.int_attributions""").df().to_dict("records")[0]
    q["completude"] = comp
    q["par_annee_source"] = con.execute("""select annee,
        count(*) as lignes,
        avg((source_dataset = 'pes_marche_2024')::int) as part_pes_2024,
        avg((offres_statut = 'ok')::int) as offres_exploitables
        from main.int_attributions group by 1 order by 1""").df().to_dict("records")
    q["sirene"] = con.execute("""select count(*) filter (where enrichi_sirene) as titulaires_enrichis,
        count(*) as titulaires,
        sum(montant_total) filter (where enrichi_sirene) / sum(montant_total) as part_montant_couverte,
        count(*) filter (where est_entrepreneur_individuel) as entrepreneurs_individuels_detectes
        from main.dim_titulaire where titulaire_key <> 'INCONNU'""").df().to_dict("records")[0]
    return q


def _pct(x: float) -> str:
    return f"{100 * x:.1f} %".replace(".", ",")


def _n(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def markdown(q: dict[str, Any]) -> str:
    L = [
        "# Rapport de qualité des données DECP",
        "",
        "> Généré par `make quality` (`python -m radar.quality`) à partir de l'entrepôt DuckDB. "
        "Ne pas modifier à la main.",
        "",
        f"- Source : [DECP consolidées – decp.info]({q['source']['dataset']}) (Licence Ouverte 2.0), "
        f"ressource du {q['source']['resource_last_modified'][:10]}, SHA-256 `{q['source']['sha256'][:16]}…`",
        f"- Lignes du fichier source : **{_n(q['lignes_source'])}** (marché × titulaire × modification)",
        f"- Dernière date de notification retenue : {q['date_max_notification']}",
        "",
        "## Entonnoir de nettoyage (lignes marché × titulaire)",
        "",
        "| Étape | Lignes |",
        "|---|---:|",
    ]
    for e in q["entonnoir"]:
        v = _n(e["lignes"])
        L.append(f"| {'**' + e['etape'] + '**' if e.get('total') else e['etape']} | {'**' + v + '**' if e.get('total') else v} |")
    m = q["marches"]
    L += [
        "",
        f"R2c – accords-cadres multi-attributaires publiés avec un identifiant par titulaire : "
        f"{_n(m['identifiants_source'])} identifiants → **{_n(m['marches_apres_r2c'])} marchés** "
        f"({_n(m['fusionnes_r2c'])} identifiants fusionnés).",
        "",
        "## Montants (règle R3)",
        "",
        "| Statut | Lignes | Part |",
        "|---|---:|---:|",
    ]
    for r in q["montant_statut"]:
        L.append(f"| {r['statut']} | {_n(r['n'])} | {_pct(r['part'])} |")
    s = q["montant_suspect"]
    L += [
        "",
        f"Les montants classés « suspects » par decp.info (comparaison aux marchés similaires) sont **conservés** : "
        f"{_n(s['n'])} lignes, {_pct(s['part_montant'])} du montant total retenu. Ils correspondent surtout à des "
        "plafonds d'accords-cadres élevés. Les montants « aberrants » sont exclus des sommes (le marché reste compté).",
        "",
        "## Nombre d'offres (règle R4)",
        "",
        "| Statut | Lignes | Part |",
        "|---|---:|---:|",
    ]
    for r in q["offres_statut"]:
        L.append(f"| {r['statut']} | {_n(r['n'])} | {_pct(r['part'])} |")
    si = q["siret"]
    L += [
        "",
        "## Identifiants (règle R5, contrôle de Luhn)",
        "",
        f"- SIRET acheteur valide : {_pct(si['acheteur_valide'])}",
        f"- Titulaires identifiés par un SIRET : {_pct(si['titulaire_type_siret'])} ; "
        f"dont SIRET invalide (clé de Luhn) : {_n(si['titulaire_siret_invalides'])} lignes",
        "",
        "## Complétude des champs clés",
        "",
        "| Champ | Taux |",
        "|---|---:|",
    ]
    for k, v in q["completude"].items():
        L.append(f"| {k} | {_pct(v)} |")
    L += [
        "",
        "## Rupture de 2024",
        "",
        "Depuis le 1er janvier 2024 (arrêtés du 22 décembre 2022), les données essentielles suivent un nouveau "
        "format et sont centralisées via le PES Marché. Le nombre de marchés publiés augmente nettement : "
        "les évolutions 2023 → 2024 mesurent autant l'amélioration de la publication que l'activité réelle.",
        "",
        "| Année | Lignes | Part issue du PES Marché 2024 | Nb d'offres exploitable |",
        "|---|---:|---:|---:|",
    ]
    for r in q["par_annee_source"]:
        L.append(f"| {r['annee']} | {_n(r['lignes'])} | {_pct(r['part_pes_2024'])} | {_pct(r['offres_exploitables'])} |")
    se = q["sirene"]
    L += [
        "",
        "## Enrichissement SIRENE",
        "",
        f"- Titulaires enrichis par l'API Recherche d'entreprises : {_n(se['titulaires_enrichis'])} sur "
        f"{_n(se['titulaires'])} (les plus importants en montant), couvrant {_pct(se['part_montant_couverte'] or 0)} "
        "du montant attribué.",
        f"- Entrepreneurs individuels détectés (noms masqués dans tous les exports) : "
        f"{_n(se['entrepreneurs_individuels_detectes'])}.",
        "- Pour les autres titulaires, la catégorie d'entreprise provient de l'enrichissement SIRENE réalisé par decp.info.",
        "",
    ]
    return "\n".join(L)


def main() -> None:
    con = duckdb.connect(str(config.WAREHOUSE), read_only=True)
    q = compute(con)
    config.SITE_DATA.mkdir(parents=True, exist_ok=True)
    (config.SITE_DATA / "qualite.json").write_text(json.dumps(q, ensure_ascii=False, default=str, indent=1))
    (config.ROOT / "docs").mkdir(exist_ok=True)
    (config.ROOT / "docs" / "qualite-donnees.md").write_text(markdown(q))
    print(markdown(q))


if __name__ == "__main__":
    main()
