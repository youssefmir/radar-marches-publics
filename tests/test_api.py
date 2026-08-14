from fastapi.testclient import TestClient

from conftest import requires_avis
from radar.api import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["statut"] == "ok"


def test_resume_sans_cle(monkeypatch):
    monkeypatch.delenv("RADAR_LLM_API_KEY", raising=False)
    import radar.api as api

    class Fake:
        avis = __import__("pandas").DataFrame([{"idweb": "1", "objet": "x", "snapshot_date": "2026-11-01"}])

    monkeypatch.setitem(api._state, "index", Fake())
    r = client.post("/api/resume", json={"idweb": "1"})
    assert r.status_code == 503
    assert "RADAR_LLM_API_KEY" in r.json()["detail"]
    monkeypatch.setitem(api._state, "index", None)


def test_profil_trop_court_refuse():
    assert client.post("/api/radar", json={"description": "x"}).status_code == 422


@requires_avis
def test_radar_classe_et_explique():
    r = client.post(
        "/api/radar?top=10",
        json={
            "description": "Nettoyage et entretien de locaux administratifs et d'écoles, vitrerie",
            "cpv": ["90911200"],
            "departements": ["59", "62"],
            "montant_min": 50000,
            "montant_max": 2000000,
        },
    )
    assert r.status_code == 200
    res = r.json()["resultats"]
    assert len(res) == 10
    scores = [x["score"] for x in res]
    assert scores == sorted(scores, reverse=True)
    for x in res:
        total = sum(c["contribution"] for c in x["composantes"].values())
        assert abs(total - x["score"]) < 0.6  # arrondis à 0,1 point
    assert any("nettoyage" in x["objet"].lower() for x in res[:5])
