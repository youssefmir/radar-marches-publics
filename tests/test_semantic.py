import yaml

from conftest import requires_warehouse
from radar import config
from radar.semantic import Semantic


def spec():
    return yaml.safe_load(config.SEMANTIC.read_text())


def test_metriques_ratio_referencent_des_mesures_existantes():
    s = spec()
    for name, m in s["metrics"].items():
        assert m["definition"].strip(), name
        if m["type"] == "ratio":
            assert m["numerator"] in s["measures"], name
            assert m.get("denominator") is None or m["denominator"] in s["measures"], name
        else:
            assert m["grain"] in ("attribution", "marche", "hhi"), name


@requires_warehouse
def test_ratios_coherents_avec_le_cube():
    sem = Semantic.load()
    direct = sem.query(["nombre_marches", "taux_offre_unique"], by=["annee"])
    cube = sem.cube(["annee", "departement"]).groupby("annee").sum(numeric_only=True)
    for _, r in direct.iterrows():
        c = cube.loc[r["annee"]]
        assert abs(c["nb_marches"] - r["nombre_marches"]) < 1e-6
        assert abs(c["nb_offre_unique"] / c["nb_marches_offres"] - r["taux_offre_unique"]) < 1e-9


@requires_warehouse
def test_indicateurs_dans_des_bornes_plausibles():
    q = Semantic.load().query(["part_pme_nombre", "taux_offre_unique", "hhi_titulaires"]).iloc[0]
    assert 0 < q["part_pme_nombre"] < 1
    assert 0 < q["taux_offre_unique"] < 1
    assert 0 <= q["hhi_titulaires"] <= 10_000
