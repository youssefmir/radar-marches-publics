"""Client HTTP robuste : réessais avec attente exponentielle, reprise des téléchargements."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

USER_AGENT = "radar-marches-publics/1.0 (+https://github.com/youssefmir/radar-marches-publics)"
_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})


def get_json(url: str, params: dict[str, Any] | None = None, retries: int = 60, timeout: int = 60) -> Any:
    """GET JSON avec réessais (les API publiques peuvent couper ou limiter le débit)."""
    delay = 1.0
    last: Exception | None = None
    for _ in range(retries):
        try:
            r = _session.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                time.sleep(float(r.headers.get("Retry-After", delay)))
                delay = min(delay * 2, 30)
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(delay)
            delay = min(delay * 1.5, 8)
    raise RuntimeError(f"Échec après {retries} tentatives : {url} ({last})")


def download(url: str, dest: Path, retries: int = 40) -> Path:
    """Télécharge un fichier en reprenant là où le transfert s'est arrêté (en-tête Range)."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    for _ in range(retries):
        done = tmp.stat().st_size if tmp.exists() else 0
        headers = {"Range": f"bytes={done}-"} if done else {}
        try:
            with _session.get(url, headers=headers, stream=True, timeout=120) as r:
                if r.status_code == 416:  # déjà complet
                    break
                r.raise_for_status()
                mode = "ab" if r.status_code == 206 else "wb"
                with open(tmp, mode) as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            break
        except requests.RequestException:
            time.sleep(3)
    else:
        raise RuntimeError(f"Téléchargement impossible : {url}")
    tmp.replace(dest)
    return dest


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
