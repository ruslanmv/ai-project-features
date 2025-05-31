"""
architecture_lookup_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **P2** – “Architecture recall”.

The goal is to surface *design-relevant* context so the downstream
planning and generation steps do not violate existing conventions.

Strategy
────────
1.  Collect candidate text chunks:  
      • Any local `docs/*.md` and `docs/*.rst` files  
      • Top-level `README.md`  
2.  Represent each chunk by an embedding vector (BeeAI or fallback).  
3.  Embed the **user prompt + constraints** as a query.  
4.  Return the *k* most similar snippets (default k=5) and stash them in
    `MEM["architecture_snippets"]`.

If BeeAI embeddings are **not** installed we fall back to a trivial
TF-IDF cosine similarity using `sklearn.feature_extraction.text`.

Environment variables
─────────────────────
`EMBED_FALLBACK_K` – override k (default 5).

Security
────────
Read-only; never executes code from the project.  All heavy lifting is
string processing.
"""

from __future__ import annotations

import glob
import logging
import os
from pathlib import Path
from typing import List, Tuple

from memory import MEM
from config import Settings

_LOG = logging.getLogger(__name__)
_CFG = Settings()

# ──────────────────────────────────────────────────────────────────────────
# Optional BeeAI embedding path
# ──────────────────────────────────────────────────────────────────────────
try:
    from beeai.embeddings import EmbeddingClient  # type: ignore
    _BEEAI_AVAILABLE = True
except ModuleNotFoundError:
    _BEEAI_AVAILABLE = False

# Fallback: sklearn TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_OK = True
except ModuleNotFoundError:
    _SKLEARN_OK = False


def run() -> None:
    """
    Execute phase P2.  Writes `architecture_snippets` (List[str]) to MEM.
    """
    user_prompt: str | None = MEM.get("user_prompt")
    tree: str | None = MEM.get("tree")
    if not user_prompt or not tree:
        _LOG.warning("architecture_lookup_agent: missing prompt or tree; nothing to do.")
        MEM.put("architecture_snippets", [])
        return

    docs = _collect_docs()
    if not docs:
        MEM.put("architecture_snippets", [])
        _LOG.info("No docs/*.md found – skipping architecture recall.")
        return

    top_k = int(os.getenv("EMBED_FALLBACK_K", 5))
    snippets: List[Tuple[str, str]] = _split_docs(docs)

    best = (
        _rank_with_beeai(user_prompt, snippets, k=top_k)
        if _BEEAI_AVAILABLE
        else _rank_with_tfidf(user_prompt, snippets, k=top_k)
    )

    only_text = [txt for _, txt in best]
    MEM.put("architecture_snippets", only_text)
    _LOG.info("Phase P2 completed – surfaced %d architecture snippets", len(only_text))


# ──────────────────────────────────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────────────────────────────────
def _collect_docs() -> List[Path]:
    """Return list of markdown/rst docs present under docs/ or project root."""
    patterns = ["docs/*.md", "docs/*.rst", "README.md"]
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend([Path(p) for p in glob.glob(pattern) if Path(p).is_file()])
    return paths


def _split_docs(paths: List[Path]) -> List[Tuple[str, str]]:
    """
    Split each doc into smaller paragraphs for finer-grained matching.

    Returns list of tuples (source_id, paragraph_text).
    """
    chunks: List[Tuple[str, str]] = []
    for p in paths:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for para in text.split("\n\n"):
            para_clean = para.strip()
            if len(para_clean) > 40:  # ignore trivial lines
                source = f"{p.name}:{hash(para_clean) & 0xffff}"
                chunks.append((source, para_clean))
    return chunks


# ── BeeAI embedding route ────────────────────────────────────────────────
def _rank_with_beeai(query: str, chunks: List[Tuple[str, str]], k: int):
    embedder = EmbeddingClient(model="mini")
    vectors = embedder.encode([c[1] for c in chunks])
    q_vec = embedder.encode([query])[0]
    # cosine similarity
    sims = [(i, (q_vec @ v) / (max((q_vec**2).sum()**0.5, 1e-8) *
                               max((v**2).sum()**0.5, 1e-8)))
            for i, v in enumerate(vectors)]
    sims.sort(key=lambda x: x[1], reverse=True)
    best = [chunks[idx] for idx, _ in sims[:k]]
    return best


# ── TF-IDF fallback ──────────────────────────────────────────────────────
def _rank_with_tfidf(query: str, chunks: List[Tuple[str, str]], k: int):
    if not _SKLEARN_OK:
        _LOG.warning("sklearn not available – returning first %d chunks", k)
        return chunks[:k]

    texts = [c[1] for c in chunks]
    vect = TfidfVectorizer(stop_words="english", max_features=5000)
    matrix = vect.fit_transform(texts + [query])
    sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    best_idx = sims.argsort()[::-1][:k]
    return [chunks[i] for i in best_idx]
