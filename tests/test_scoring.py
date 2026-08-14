import datetime as dt
import math

import pandas as pd
import pytest

from radar.scoring import (
    Profil,
    concurrence_score,
    cpv_match,
    geo_match,
    go_no_go,
    sortant_score,
    taille_match,
    verdict,
)


@pytest.mark.parametrize(
    ("profil", "avis", "attendu"),
    [
        (["45262500"], ["45262500"], 1.0),
        (["45262500"], ["45262000"], 0.8),
        (["45262500"], ["45231000"], 0.6),
        (["45262500"], ["45110000"], 0.3),
        (["45262500"], ["90911200"], 0.0),
        (["45262500"], [], 0.0),
    ],
)
def test_cpv_hierarchique(profil, avis, attendu):
    assert cpv_match(profil, avis) == attendu


def test_geographie():
    assert geo_match(["93"], ["93", "75"]) == 1.0
    assert geo_match(["93"], ["77"]) == 0.6  # même région (Île-de-France)
    assert geo_match(["93"], ["13"]) == 0.0
    assert geo_match(["93"], []) == 0.3
    assert geo_match([], ["13"]) == 1.0


def test_taille():
    assert taille_match(500_000, 100_000, 3_000_000) == 1.0
    assert taille_match(None, 100_000, 3_000_000) == 0.5
    assert taille_match(float("nan"), 1, 2) == 0.5
    assert 0 < taille_match(10_000_000, 100_000, 3_000_000) < 0.5
    assert taille_match(30_000_000, 100_000, 3_000_000) < taille_match(10_000_000, 100_000, 3_000_000)


def test_concurrence_et_sortant_monotones():
    assert concurrence_score(1) > concurrence_score(5) > concurrence_score(15)
    assert math.isclose(concurrence_score(5), 0.5)
    assert concurrence_score(None) == 0.5
    assert sortant_score(0.9, 10) < sortant_score(0.2, 10)
    assert sortant_score(0.9, 2) == 0.7  # trop peu d'historique : neutre


def test_go_no_go_et_verdict():
    row = pd.Series(
        {
            "date_limite": "2026-11-05T12:00:00+00:00",
            "procedure": "Procédure ouverte",
            "type_procedure": "OUVERT",
            "nb_lots": 3,
            "montant_estime": 50_000.0,
            "ponderation_prix": 70.0,
            "criteres": None,
            "duree_mois": 12.0,
        }
    )
    p = Profil(nom="Test", description="x", montant_min=100_000, montant_max=1_000_000)
    items = go_no_go(row, p, dt.date(2026, 11, 1))
    statut = {i["critere"]: i["statut"] for i in items}
    assert statut["Date limite"] == "risque"  # 4 jours
    assert statut["Allotissement"] == "ok"
    assert statut["Montant estimé"] == "attention"
    assert statut["Poids du prix"] == "attention"
    assert verdict(items) == "no-go probable"


def test_profil_from_dict_ignore_les_champs_inconnus():
    p = Profil.from_dict({"nom": "A", "description": "B", "cpv": ["1"], "effectif": 80})
    assert p.extra == {"effectif": 80}
