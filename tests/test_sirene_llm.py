import pytest

from radar import llm
from radar.sirene import parse_result


def test_parse_result_entrepreneur_individuel():
    payload = {
        "results": [
            {
                "siren": "123456789",
                "nom_complet": "JEAN DUPONT",
                "nature_juridique": "1000",
                "categorie_entreprise": "PME",
                "siege": {"region": "11"},
            }
        ]
    }
    r = parse_result("123456789", payload)
    assert r["found"] and r["est_entrepreneur_individuel"]


def test_parse_result_non_trouve():
    assert parse_result("123456789", {"results": [{"siren": "999999999"}]}) == {
        "siren": "123456789",
        "found": False,
        "retrieved_at": parse_result("123456789", None)["retrieved_at"],
    }


def test_sans_cle_aucun_resume(monkeypatch):
    monkeypatch.delenv("RADAR_LLM_API_KEY", raising=False)
    with pytest.raises(llm.LLMIndisponible):
        llm.resumer({"objet": "Test"})


def test_resume_renvoie_la_sortie_reelle_du_fournisseur(monkeypatch):
    class Rep:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "- Objet : test"}}]}

    appels = {}

    def fake_post(url, headers, json, timeout):
        appels["url"] = url
        appels["model"] = json["model"]
        return Rep()

    monkeypatch.setattr(llm.requests, "post", fake_post)
    out = llm.resumer({"objet": "Test"}, llm.LLMConfig("cle", "https://exemple.invalid/v1", "modele-x"))
    assert out == {"resume": "- Objet : test", "modele": "modele-x"}
    assert appels["url"] == "https://exemple.invalid/v1/chat/completions"
