"""Extraction compacte de l'historique DECP utile au radar (versionnée dans data/history/).

- concurrence_acheteur_cpv.parquet : acheteur × groupe CPV (nb marchés, offres moyennes, taux d'offre unique,
  titulaire principal et sa part) ;
- concurrence_dep_cpv.parquet : repli département × groupe CPV quand l'acheteur a trop peu d'historique ;
- acheteurs.parquet : SIRET, nom normalisé, département (pour rapprocher les avis BOAMP des acheteurs DECP).

Usage : python -m radar.history
"""

from __future__ import annotations

import duckdb

from . import config

HISTORY = config.DATA / "history"
NORMALISE = "trim(regexp_replace(lower(strip_accents(coalesce({c}, ''))), '[^a-z0-9]+', ' ', 'g'))"


def build() -> None:
    HISTORY.mkdir(exist_ok=True)
    con = duckdb.connect(str(config.WAREHOUSE), read_only=True)
    con.execute(f"""
        copy (
            select c.acheteur_id, c.groupe_cpv, c.nb_marches, c.nb_marches_offres,
                   round(c.offres_moyennes, 2) as offres_moyennes, round(c.taux_offre_unique, 3) as taux_offre_unique,
                   c.montant_median, c.derniere_attribution,
                   case when t.est_entrepreneur_individuel or c.titulaire_principal_key = 'INCONNU' then null
                        else t.titulaire_nom_affichable end as titulaire_principal_nom,
                   t.categorie as titulaire_principal_categorie,
                   c.titulaire_principal_nb_marches, round(c.titulaire_principal_part, 3) as titulaire_principal_part
            from main.int_concurrence_acheteur_cpv c
            left join main.dim_titulaire t on t.titulaire_key = c.titulaire_principal_key
            order by 1, 2
        ) to '{HISTORY / "concurrence_acheteur_cpv.parquet"}' (format parquet, compression zstd)
    """)
    con.execute(f"""
        copy (
            select f.departement_code, substr(f.code_cpv, 1, 3) as groupe_cpv,
                   count(distinct f.marche_uid) as nb_marches,
                   round(sum(f.offres_recues * f.poids_marche) / nullif(sum(case when f.offres_recues is not null then f.poids_marche end), 0), 2) as offres_moyennes,
                   round(sum(case when f.offres_recues = 1 then f.poids_marche end) / nullif(sum(case when f.offres_recues is not null then f.poids_marche end), 0), 3) as taux_offre_unique,
                   sum(case when f.offres_recues is not null then f.poids_marche end) as nb_marches_offres
            from main.fct_attributions f
            group by 1, 2 order by 1, 2
        ) to '{HISTORY / "concurrence_dep_cpv.parquet"}' (format parquet, compression zstd)
    """)
    con.execute(f"""
        copy (
            select acheteur_id, acheteur_nom, {NORMALISE.format(c="acheteur_nom")} as nom_normalise,
                   departement_code, acheteur_categorie, nb_marches
            from main.dim_acheteur order by 1
        ) to '{HISTORY / "acheteurs.parquet"}' (format parquet, compression zstd)
    """)
    for f in sorted(HISTORY.glob("*.parquet")):
        print(f"{f.name}: {f.stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    build()
