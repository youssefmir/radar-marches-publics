"""Application locale : sert le site construit et une API pour le radar en direct.

Lancement : make app  (équivaut à `uvicorn radar.api:app --port 8000`), puis
http://127.0.0.1:8000/radar-marches-publics/
"""

from __future__ import annotations

import datetime as dt
import threading
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import boamp, config, download
from .index import AvisIndex, load_avis
from .llm import LLMIndisponible, resumer
from .scoring import Profil, load_config, rank

DIST = config.ROOT / "web" / "dist"
BASE = "/radar-marches-publics"

app = FastAPI(title="Radar Marchés Publics", version="1.0.0")
_state: dict[str, Any] = {"index": None, "refresh": {"etat": "inactif"}}
_lock = threading.Lock()


def get_index() -> AvisIndex:
    with _lock:
        if _state["index"] is None:
            _state["index"] = AvisIndex(load_avis())
        return _state["index"]


class ProfilIn(BaseModel):
    nom: str = "Mon entreprise"
    description: str = Field(min_length=10, max_length=4000)
    cpv: list[str] = []
    departements: list[str] = []
    montant_min: float | None = None
    montant_max: float | None = None


class ResumeIn(BaseModel):
    idweb: str


@app.get("/api/health")
def health() -> dict:
    idx = _state["index"]
    return {
        "statut": "ok",
        "index_charge": idx is not None,
        "snapshot_date": idx.avis["snapshot_date"].iat[0] if idx is not None else None,
    }


@app.post("/api/radar")
def radar(p: ProfilIn, top: int = 30) -> dict:
    cpv = [c for c in p.cpv if c.isdigit() and len(c) == 8]
    profil = Profil(
        nom=p.nom,
        description=p.description,
        cpv=cpv,
        departements=[d.upper() for d in p.departements],
        montant_min=p.montant_min,
        montant_max=p.montant_max,
        id="personnalise",
    )
    idx = get_index()
    res = rank(idx, profil, load_config()["poids"], top=min(max(top, 1), 100))
    return {
        "snapshot_date": idx.avis["snapshot_date"].iat[0],
        "profil": profil.__dict__ | {"extra": None},
        "resultats": res,
    }


@app.post("/api/resume")
def resume(body: ResumeIn) -> dict:
    av = get_index().avis
    hit = av[av["idweb"] == body.idweb]
    if hit.empty:
        raise HTTPException(404, "Avis introuvable dans l'instantané")
    try:
        return resumer(hit.iloc[0].to_dict())
    except LLMIndisponible as exc:
        raise HTTPException(503, str(exc)) from exc


def _refresh() -> None:
    try:
        _state["refresh"] = {"etat": "téléchargement", "debut": dt.datetime.now().isoformat(timespec="seconds")}
        src = download.fetch_boamp()
        _state["refresh"]["etat"] = "indexation"
        df = boamp.flatten(src)
        df.to_parquet(config.INTERIM / "boamp_avis.parquet", index=False)
        new = AvisIndex(load_avis())
        with _lock:
            _state["index"] = new
        _state["refresh"] = {"etat": "terminé", "snapshot_date": df["snapshot_date"].iat[0], "avis": int(len(new.avis))}
    except Exception as exc:  # l'erreur est rapportée à l'interface, le serveur continue
        _state["refresh"] = {"etat": "échec", "erreur": str(exc)}


@app.post("/api/boamp/refresh", status_code=202)
def refresh() -> dict:
    if _state["refresh"].get("etat") in ("téléchargement", "indexation"):
        return _state["refresh"]
    threading.Thread(target=_refresh, daemon=True).start()
    return {"etat": "démarré"}


@app.get("/api/boamp/status")
def refresh_status() -> dict:
    return _state["refresh"]


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(f"{BASE}/")


@app.get(f"{BASE}/", include_in_schema=False)
def index_html() -> HTMLResponse:
    page = DIST / "index.html"
    if not page.exists():
        raise HTTPException(503, "Site non construit : lancez `make site`.")
    html = page.read_text(encoding="utf-8").replace("<head>", '<head>\n    <meta name="radar-api" content="/api" />', 1)
    return HTMLResponse(html)


if DIST.exists():
    app.mount(BASE, StaticFiles(directory=DIST, html=True), name="site")
