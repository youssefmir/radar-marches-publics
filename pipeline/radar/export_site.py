"""Exports compacts pour le site statique (web/public/data), tous issus de la couche sémantique.

Usage : python -m radar.export_site [--sans-radar]
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from typing import Any

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import config
from .semantic import FROM, Semantic

OUT = config.SITE_DATA
CUBE_DIMS = ["annee", "departement", "division_cpv", "procedure", "categorie_acheteur", "type_marche"]
N_FICHES = 1000


def _clean(o: Any) -> Any:
    """NaN -> None, numpy -> types natifs, arrondis raisonnables pour alléger le JSON."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list | tuple):
        return [_clean(v) for v in o]
    if hasattr(o, "item"):
        o = o.item()
    if isinstance(o, float):
        return None if math.isnan(o) else round(o, 4)
    return o


def write_json(name: str, data: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(data), ensure_ascii=False, separators=(",", ":"), default=str))


def export_cube(sem: Semantic) -> int:
    cube = sem.cube(CUBE_DIMS)
    for c in cube.columns:
        if c not in CUBE_DIMS:
            cube[c] = cube[c].astype("float64").round(4)
    cube["annee"] = cube["annee"].astype("int16")
    table = pa.Table.from_pandas(cube, preserve_index=False)
    pq.write_table(table, OUT / "cube.parquet", compression="snappy", row_group_size=50_000)
    return len(cube)


def export_dimensions(con: duckdb.DuckDBPyConnection) -> None:
    geo = con.execute("select * from main.dim_geo order by code_departement").df()
    regions = geo.drop_duplicates("code_region")[["code_region", "nom_region"]].sort_values("nom_region")
    div = con.execute("""select division_code as code, division_libelle as libelle, type_cpv
                         from main.dim_cpv where code_cpv = division_code || '000000' or code_cpv = '00000000'
                         order by 1""").df()
    proc = con.execute("select * from main.dim_procedure order by ordre").df()
    write_json(
        "dimensions.json",
        {
            "departements": geo.to_dict("records"),
            "regions": regions.to_dict("records"),
            "divisions_cpv": div.to_dict("records"),
            "procedures": proc.to_dict("records"),
        },
    )


def export_non_additifs(sem: Semantic) -> None:
    m = ["montant_median", "hhi_titulaires", "nb_acheteurs", "nb_titulaires"]
    out = {"national": sem.query(m).iloc[0].to_dict()}
    for by in ("annee", "region", "division_cpv", "type_marche", "procedure", "categorie_acheteur"):
        out[by] = sem.query(m, by=[by]).to_dict("records")
    # Concurrence par division CPV sur la période où le nombre d'offres est majoritairement renseigné (2024+).
    out["periode_concurrence"] = "2024 et après"
    out["concurrence_division_2024"] = sem.query(
        ["nombre_marches", "offres_moyennes", "taux_offre_unique", "taux_renseignement_offres"],
        by=["division_cpv"],
        where={"annee": [2024, 2025, 2026]},
    ).to_dict("records")
    out["concurrence_region_2024"] = sem.query(
        ["nombre_marches", "offres_moyennes", "taux_offre_unique", "taux_renseignement_offres"],
        by=["region"],
        where={"annee": [2024, 2025, 2026]},
    ).to_dict("records")
    write_json("non_additifs.json", out)


def export_acheteurs(con: duckdb.DuckDBPyConnection) -> int:
    fiches_dir = OUT / "acheteurs"
    shutil.rmtree(fiches_dir, ignore_errors=True)
    fiches_dir.mkdir(parents=True)
    top = con.execute(f"""
        select a.acheteur_id, a.acheteur_nom, a.acheteur_categorie, a.departement_code, g.nom_departement,
               g.nom_region, count(distinct f.marche_uid) as nb_marches, sum(f.montant_part) as montant_total,
               sum(case when f.categorie_titulaire = 'PME' then f.poids_marche end)
                 / nullif(sum(case when f.categorie_titulaire in ('PME', 'ETI', 'GE') then f.poids_marche end), 0) as part_pme,
               sum(f.offres_recues * f.poids_marche) / nullif(sum(case when f.offres_recues is not null then f.poids_marche end), 0) as offres_moyennes,
               sum(case when f.offres_recues = 1 then f.poids_marche end)
                 / nullif(sum(case when f.offres_recues is not null then f.poids_marche end), 0) as taux_offre_unique
        from main.fct_attributions f
        join main.dim_acheteur a using (acheteur_id)
        join main.dim_geo g on g.code_departement = a.departement_code
        group by all
        order by nb_marches desc
        limit {N_FICHES}
    """).df()
    write_json("acheteurs.json", top.to_dict("records"))
    ids = top["acheteur_id"].tolist()
    con.execute("create or replace temp table sel as select unnest(?) as acheteur_id", [ids])
    par_cpv = con.execute("""
        select f.acheteur_id, c.groupe_code, any_value(c.groupe_libelle) as groupe_libelle,
               count(distinct f.marche_uid) as nb_marches, median(f.montant_marche) as montant_median,
               sum(f.offres_recues * f.poids_marche) / nullif(sum(case when f.offres_recues is not null then f.poids_marche end), 0) as offres_moyennes,
               sum(case when f.offres_recues = 1 then f.poids_marche end)
                 / nullif(sum(case when f.offres_recues is not null then f.poids_marche end), 0) as taux_offre_unique,
               sum(case when f.categorie_titulaire = 'PME' then f.poids_marche end)
                 / nullif(sum(case when f.categorie_titulaire in ('PME', 'ETI', 'GE') then f.poids_marche end), 0) as part_pme
        from main.fct_attributions f join sel using (acheteur_id) join main.dim_cpv c using (code_cpv)
        group by 1, 2
    """).df()
    par_annee = con.execute("""
        select f.acheteur_id, f.annee, count(distinct f.marche_uid) as nb_marches, sum(f.montant_part) as montant
        from main.fct_attributions f join sel using (acheteur_id) group by 1, 2 order by 1, 2
    """).df()
    tit = con.execute("""
        select f.acheteur_id,
               case when t.nom_publiable then t.titulaire_nom_affichable else 'Titulaire non affiché (personne physique possible)' end as titulaire,
               t.nom_publiable, t.categorie, count(distinct f.marche_uid) as nb_marches, sum(f.montant_part) as montant
        from main.fct_attributions f join sel using (acheteur_id) join main.dim_titulaire t using (titulaire_key)
        where f.titulaire_key <> 'INCONNU'
        group by 1, 2, 3, 4
        qualify row_number() over (partition by f.acheteur_id order by count(distinct f.marche_uid) desc, sum(f.montant_part) desc) <= 8
    """).df()
    recents = con.execute("""
        select m.acheteur_id, m.date_notification, m.objet, m.montant_marche, m.offres_recues, m.code_cpv, m.procedure_code
        from main.mart_marches m join sel using (acheteur_id)
        qualify row_number() over (partition by m.acheteur_id order by m.date_notification desc, m.marche_uid) <= 10
    """).df()
    for a in top.to_dict("records"):
        aid = a["acheteur_id"]
        fiche = {
            **a,
            "par_cpv": par_cpv[par_cpv.acheteur_id == aid]
            .drop(columns="acheteur_id")
            .sort_values("nb_marches", ascending=False)
            .head(15)
            .to_dict("records"),
            "par_annee": par_annee[par_annee.acheteur_id == aid].drop(columns="acheteur_id").to_dict("records"),
            "titulaires": tit[tit.acheteur_id == aid]
            .drop(columns="acheteur_id")
            .sort_values(["nb_marches", "montant"], ascending=False)
            .to_dict("records"),
            "marches_recents": recents[recents.acheteur_id == aid]
            .drop(columns="acheteur_id")
            .sort_values("date_notification", ascending=False)
            .to_dict("records"),
        }
        write_json(f"acheteurs/{aid}.json", fiche)
    return len(top)


def export_meta(con: duckdb.DuckDBPyConnection, sem: Semantic, n_cube: int) -> None:
    lock = json.loads(config.SOURCES_LOCK.read_text())
    avis = pd.read_parquet(config.INTERIM / "boamp_avis.parquet")
    ouverts = avis[avis["exclu_motif"].isna()]
    write_json(
        "meta.json",
        {
            "decp": {
                "version": lock["decp"]["resource_last_modified"][:10],
                "url": lock["decp"]["dataset"],
                "date_max_notification": str(
                    con.execute(
                        "select max(date) from main.dim_date d join main.fct_attributions f using (date_key)"
                    ).fetchone()[0]
                ),
            },
            "boamp": {
                "snapshot_date": lock["boamp"]["snapshot_date"],
                "avis_instantane": int(len(avis)),
                "avis_ouverts_retenus": int(len(ouverts)),
                "par_type": ouverts["type_marche"].fillna("Non renseigné").value_counts().to_dict(),
            },
            "cube_lignes": n_cube,
            "periode": sem.spec["periode"],
        },
    )
    write_json("metrics.json", sem.catalog())


def export_radar() -> None:
    from .index import AvisIndex, load_avis
    from .scoring import COMPOSANTES, Profil, load_config, rank

    cfg = load_config()
    idx = AvisIndex(load_avis())
    snapshot = idx.avis["snapshot_date"].iat[0]
    profils = []
    for p in cfg["profils"]:
        res = rank(idx, Profil.from_dict(p), cfg["poids"], top=30)
        write_json(f"radar/{p['id']}.json", {"snapshot_date": snapshot, "profil": p, "resultats": res})
        profils.append({k: p[k] for k in ("id", "nom", "secteur", "effectif", "ville", "fictif")})
    write_json(
        "radar/index.json",
        {
            "snapshot_date": snapshot,
            "profils": profils,
            "poids": cfg["poids"],
            "composantes": COMPOSANTES,
            "nb_avis": len(idx.avis),
        },
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sans-radar", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sem = Semantic.load()
    con = sem.con
    n = export_cube(sem)
    export_dimensions(con)
    export_non_additifs(sem)
    nf = export_acheteurs(con)
    export_meta(con, sem, n)
    if not args.sans_radar:
        export_radar()
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"cube : {n} lignes ; fiches acheteurs : {nf} ; exports : {total / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()

__all__ = ["FROM"]
