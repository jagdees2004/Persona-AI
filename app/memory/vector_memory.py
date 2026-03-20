"""
Long-term vector memory using ChromaDB + sentence-transformers.
Persona-isolated via metadata filtering on user_id + persona.
"""

import logging
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-loaded globals
_chroma_client = None
_collection = None

COLLECTION_NAME = "persona_memories"


def _get_client():
    """Lazy-load the ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        logger.info(f"ChromaDB client initialized at: {settings.CHROMA_PERSIST_DIR}")
    return _chroma_client


def _get_collection():
    """Get or create the ChromaDB collection with sentence-transformer embeddings."""
    global _collection
    if _collection is None:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready ({_collection.count()} vectors)")
    return _collection


def store_embedding(
    user_id: str,
    persona: str,
    text: str,
    doc_id: str,
) -> None:
    """
    Store a text with metadata in ChromaDB.
    ChromaDB handles embedding automatically via the configured embedding function.
    """
    collection = _get_collection()
    collection.add(
        documents=[text],
        ids=[doc_id],
        metadatas=[{"user_id": user_id, "persona": persona}],
    )
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
    collection = _get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"$and": [{"user_id": user_id}, {"persona": persona}]},
    )

    memories = []
    if results and results["documents"] and results["documents"][0]:
        docs = results["documents"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        for doc, dist in zip(docs, distances):
            # ChromaDB returns distances (lower = more similar for cosine)
            # Convert to similarity score
            score = round(1.0 - dist, 4)
            memories.append({"text": doc, "score": score})

    return memories


def delete_user_persona_memory(user_id: str, persona: str) -> int:
    """
    Delete all long-term memory entries for a user+persona pair.
    """
    collection = _get_collection()

    # Get all IDs matching this user+persona
    try:
        results = collection.get(
            where={"$and": [{"user_id": user_id}, {"persona": persona}]},
        )
    except Exception:
        return 0

    if not results or not results["ids"]:
        return 0

    ids_to_delete = results["ids"]
    count = len(ids_to_delete)
    collection.delete(ids=ids_to_delete)

    logger.info(f"Deleted {count} long-term memories for user={user_id}, persona={persona}")
    return count


def get_memory_count(user_id: str, persona: str) -> int:
    """Get count of stored memories for a user+persona."""
    collection = _get_collection()
    try:
        results = collection.get(
            where={"$and": [{"user_id": user_id}, {"persona": persona}]},
        )
        return len(results["ids"]) if results and results["ids"] else 0
    except Exception:
        return 0
