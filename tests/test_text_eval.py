import numpy as np

from radar.evaluate import ndcg_at, precision_at, recall_at, split_of
from radar.index import minmax
from radar.text import tokenize


def test_tokenize_retire_accents_mots_vides_et_pluriels():
    t = tokenize("Travaux de rénovation énergétique des écoles")
    assert "de" not in t and "des" not in t
    assert "renov" in t  # racinisation légère
    assert tokenize("écoles") == tokenize("ecole")


def test_metriques_de_classement():
    rel = np.array([1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], dtype=float)
    assert precision_at(rel) == 0.2
    assert recall_at(rel, n_rel=3, k=50) == 1.0
    parfait = np.array([1, 1, 1, 0], dtype=float)
    assert ndcg_at(parfait, n_rel=3) == 1.0
    assert 0 < ndcg_at(rel, n_rel=3) < 1


def test_partition_deterministe():
    assert split_of("26-101741") == split_of("26-101741")
    parts = [split_of(f"26-{i}") for i in range(2000)]
    assert 0.25 < parts.count("reglage") / len(parts) < 0.35


def test_minmax():
    assert list(minmax(np.array([2.0, 4.0, 6.0]))) == [0.0, 0.5, 1.0]
    assert list(minmax(np.array([3.0, 3.0]))) == [0.0, 0.0]
