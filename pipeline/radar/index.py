"""Index de recherche sur les avis : BM25 (lexical) et embeddings (sémantique), avec cache disque."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

from . import config
from .text import tokenize

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
# Les modèles e5 attendent des préfixes distincts pour la requête et le passage.
PREFIXES = {"intfloat/multilingual-e5-small": ("query: ", "passage: ")}


def doc_text(row: pd.Series, max_desc: int = 1200) -> str:
    """Texte indexé d'un avis : objet + description (sans les libellés CPV, pour ne pas biaiser l'évaluation)."""
    objet = row.get("objet") or ""
    desc = (row.get("description") or "")[:max_desc]
    if desc.lower().startswith(objet.lower()[:40]):
        return desc
    return f"{objet}. {desc}".strip()


def load_avis(include_excluded: bool = False) -> pd.DataFrame:
    df = pd.read_parquet(config.INTERIM / "boamp_avis.parquet")
    if not include_excluded:
        df = df[df["exclu_motif"].isna()]
    df = df.reset_index(drop=True)
    df["texte"] = df.apply(doc_text, axis=1)
    return df


@lru_cache(maxsize=2)
def get_model(name: str = DEFAULT_MODEL):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name, device="cpu")


def encode(texts: list[str], model: str = DEFAULT_MODEL, kind: str = "passage", batch_size: int = 64) -> np.ndarray:
    q, p = PREFIXES.get(model, ("", ""))
    prefix = q if kind == "query" else p
    m = get_model(model)
    m.max_seq_length = 256
    emb = m.encode(
        [prefix + t for t in texts], batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
    )
    return np.asarray(emb, dtype=np.float32)


@dataclass
class AvisIndex:
    avis: pd.DataFrame
    model: str = DEFAULT_MODEL
    emb: np.ndarray = field(init=False)
    bm25: BM25Okapi = field(init=False)

    def __post_init__(self) -> None:
        texts = self.avis["texte"].tolist()
        key = hashlib.sha1(("\n".join(self.avis["idweb"]) + self.model).encode()).hexdigest()[:12]
        cache = config.CACHE / f"emb_{self.model.split('/')[-1]}_{key}.npy"
        if cache.exists():
            self.emb = np.load(cache)
        else:
            self.emb = encode(texts, self.model, "passage")
            np.save(cache, self.emb)
        self.bm25 = BM25Okapi([tokenize(t) or ["_"] for t in texts])

    def semantic_scores(self, query: str) -> np.ndarray:
        q = encode([query], self.model, "query")[0]
        return self.emb @ q

    def lexical_scores(self, query: str) -> np.ndarray:
        return np.asarray(self.bm25.get_scores(tokenize(query)), dtype=np.float32)


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(np.min(x)), float(np.max(x))
    return np.zeros_like(x) if hi - lo < 1e-12 else (x - lo) / (hi - lo)
