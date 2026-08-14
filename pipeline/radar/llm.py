"""Résumé optionnel d'un avis par un LLM (Mistral ou tout point d'accès compatible OpenAI).

La clé est fournie par l'utilisateur (variable d'environnement RADAR_LLM_API_KEY). Sans clé, aucune
sortie n'est produite ni simulée : l'API renvoie une erreur explicite.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
DEFAULT_MODEL = "mistral-small-latest"
PROMPT = (
    "Tu es un assistant de veille sur les marchés publics pour une PME. À partir de l'avis ci-dessous, "
    "rédige un résumé factuel en français de 5 puces au maximum : objet, acheteur, lots, critères et "
    "date limite. N'invente aucune information absente de l'avis ; écris « non précisé » si besoin.\n\n"
)


class LLMIndisponible(RuntimeError):
    """Aucune clé configurée ou fournisseur injoignable."""


@dataclass
class LLMConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL

    @classmethod
    def from_env(cls) -> LLMConfig | None:
        key = os.environ.get("RADAR_LLM_API_KEY", "").strip()
        if not key:
            return None
        return cls(
            key,
            os.environ.get("RADAR_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            os.environ.get("RADAR_LLM_MODEL", DEFAULT_MODEL),
        )


def texte_avis(avis: dict) -> str:
    champs = [
        ("Objet", avis.get("objet")),
        ("Acheteur", avis.get("acheteur_nom")),
        ("Date limite", avis.get("date_limite")),
        ("Procédure", avis.get("procedure")),
        ("Nombre de lots", avis.get("nb_lots")),
        ("Critères", avis.get("criteres")),
        ("Description", (avis.get("description") or "")[:3000]),
    ]
    return "\n".join(f"{k} : {v}" for k, v in champs if v)


def resumer(avis: dict, cfg: LLMConfig | None = None, timeout: int = 60) -> dict:
    cfg = cfg or LLMConfig.from_env()
    if cfg is None:
        raise LLMIndisponible("Aucune clé LLM configurée (variable RADAR_LLM_API_KEY) : résumé désactivé.")
    try:
        r = requests.post(
            f"{cfg.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
            json={
                "model": cfg.model,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": PROMPT + texte_avis(avis)}],
            },
            timeout=timeout,
        )
        r.raise_for_status()
        contenu = r.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        raise LLMIndisponible(f"Le fournisseur LLM n'a pas répondu correctement : {exc}") from exc
    return {"resume": contenu, "modele": cfg.model}
