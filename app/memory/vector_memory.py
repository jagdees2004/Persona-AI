"""
Long-term vector memory using FAISS + sentence-transformers.
Persona-isolated via metadata filtering on user_id + persona.
Uses a single FAISS index with metadata-based filtering.
"""

import logging
import os
import json
import pickle
import numpy as np
from typing import Optional
from pathlib import Path
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-loaded globals
_index = None
_embedder = None
_metadata: list[dict] = []  # [{id, user_id, persona, text}, ...]
_persist_dir = None

METADATA_FILE = "metadata.pkl"
INDEX_FILE = "index.faiss"


def _get_persist_dir() -> Path:
    """Get the persistence directory for FAISS data."""
    global _persist_dir
    if _persist_dir is None:
        _persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        _persist_dir.mkdir(parents=True, exist_ok=True)
    return _persist_dir


def _get_embedder():
    """Lazy-load the sentence transformer model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
    return _embedder


def _load_index():
    """Load FAISS index and metadata from disk if they exist."""
    global _index, _metadata
    import faiss

    persist_dir = _get_persist_dir()
    index_path = persist_dir / INDEX_FILE
    meta_path = persist_dir / METADATA_FILE

    if index_path.exists() and meta_path.exists():
        _index = faiss.read_index(str(index_path))
        with open(meta_path, "rb") as f:
            _metadata = pickle.load(f)
        logger.info(f"Loaded FAISS index with {_index.ntotal} vectors")
    else:
        # Create empty index — dimension will be set on first add
        _index = None
        _metadata = []
        logger.info("No existing FAISS index found, starting fresh")


def _save_index():
    """Persist FAISS index and metadata to disk."""
    import faiss

    if _index is None:
        return

    persist_dir = _get_persist_dir()
    faiss.write_index(_index, str(persist_dir / INDEX_FILE))
    with open(persist_dir / METADATA_FILE, "wb") as f:
        pickle.dump(_metadata, f)
    logger.debug(f"Saved FAISS index with {_index.ntotal} vectors")


def _ensure_index_loaded():
    """Ensure the index is loaded from disk."""
    global _index
    if _index is None and _metadata == []:
        _load_index()


def store_embedding(
    user_id: str,
    persona: str,
    text: str,
    doc_id: str,
) -> None:
    """
    Store a text with metadata in FAISS.
    Embeds the text and adds to the flat index.
    """
    import faiss
    global _index, _metadata

    _ensure_index_loaded()

    embedder = _get_embedder()
    embedding = embedder.encode([text], normalize_embeddings=True)
    embedding = np.array(embedding, dtype=np.float32)

    dim = embedding.shape[1]

    if _index is None:
        _index = faiss.IndexFlatIP(dim)  # Inner product (cosine for normalized vectors)
        logger.info(f"Created FAISS index with dimension {dim}")

    _index.add(embedding)
    _metadata.append({
        "id": doc_id,
        "user_id": user_id,
        "persona": persona,
        "text": text,
    })

    _save_index()
    logger.debug(f"Stored embedding for user={user_id}, persona={persona}, id={doc_id}")


def search(
    query: str,
    user_id: str,
    persona: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Search long-term memory filtered by BOTH user_id AND persona.
    Returns list of {"text": str, "score": float}.
    """
    global _index, _metadata

    _ensure_index_loaded()

    if _index is None or _index.ntotal == 0:
        return []

    embedder = _get_embedder()
    query_vec = embedder.encode([query], normalize_embeddings=True)
    query_vec = np.array(query_vec, dtype=np.float32)

    # Search more results than needed, then filter by metadata
    search_k = min(_index.ntotal, top_k * 10)
    scores, indices = _index.search(query_vec, search_k)

    memories = []
    for i, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(_metadata):
            continue

        meta = _metadata[idx]
        # STRICT filter: BOTH user_id AND persona must match
        if meta["user_id"] == user_id and meta["persona"] == persona:
            memories.append({
                "text": meta["text"],
                "score": round(float(scores[0][i]), 4),
            })
            if len(memories) >= top_k:
                break

    return memories


def delete_user_persona_memory(user_id: str, persona: str) -> int:
    """
    Delete all long-term memory entries for a user+persona pair.
    Since FAISS doesn't support deletion, we rebuild the index without matching entries.
    """
    import faiss
    global _index, _metadata

    _ensure_index_loaded()

    if _index is None or not _metadata:
        return 0

    # Find indices to keep
    keep_indices = []
    removed_count = 0
    for i, meta in enumerate(_metadata):
        if meta["user_id"] == user_id and meta["persona"] == persona:
            removed_count += 1
        else:
            keep_indices.append(i)

    if removed_count == 0:
        return 0

    if not keep_indices:
        # All entries were for this user+persona — reset everything
        _index = None
        _metadata = []
    else:
        # Rebuild index with remaining entries
        embedder = _get_embedder()
        remaining_texts = [_metadata[i]["text"] for i in keep_indices]
        remaining_meta = [_metadata[i] for i in keep_indices]

        embeddings = embedder.encode(remaining_texts, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        dim = embeddings.shape[1]
        new_index = faiss.IndexFlatIP(dim)
        new_index.add(embeddings)

        _index = new_index
        _metadata = remaining_meta

    _save_index()
    logger.info(f"Deleted {removed_count} long-term memories for user={user_id}, persona={persona}")
    return removed_count


def get_memory_count(user_id: str, persona: str) -> int:
    """Get count of stored memories for a user+persona."""
    _ensure_index_loaded()
    return sum(
        1 for m in _metadata
        if m["user_id"] == user_id and m["persona"] == persona
    )
