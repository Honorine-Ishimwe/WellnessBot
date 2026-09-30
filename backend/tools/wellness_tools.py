"""
Wellness tool implementations — the actual functions called by the agent.
Each function returns a JSON-serializable dict.
"""

import os
import json
import pickle

import numpy as np
from openai import OpenAI

from backend.config import (
    FAISS_INDEX_DIR,
    EMBEDDING_MODEL,
    RAG_TOP_K,
    RAG_SIMILARITY_THRESHOLD,
)
from backend.services import goal_service
from backend.middleware.logging import logger

# ── FAISS index (lazy loaded singleton) ───────────────

_faiss_index = None
_faiss_metadata = None
_embed_client = OpenAI()

FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "wellness.faiss")
METADATA_PATH = os.path.join(FAISS_INDEX_DIR, "wellness_metadata.pkl")


def _load_faiss():
    """Lazy-load the FAISS index and metadata."""
    global _faiss_index, _faiss_metadata

    if _faiss_index is not None:
        return _faiss_index, _faiss_metadata

    import faiss

    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(
            f"FAISS index not found at {FAISS_INDEX_PATH}. "
            "Run 'python -m backend.tools.build_index' first."
        )

    _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    with open(METADATA_PATH, "rb") as f:
        _faiss_metadata = pickle.load(f)

    logger.info(f"[RAG] Loaded FAISS index with {_faiss_index.ntotal} vectors")
    return _faiss_index, _faiss_metadata


def _get_query_embedding(query):
    """Generate an embedding for a search query."""
    response = _embed_client.embeddings.create(
        input=[query],
        model=EMBEDDING_MODEL,
    )
    embedding = np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)
    import faiss
    faiss.normalize_L2(embedding)
    return embedding


# ── Tool: search_knowledge_base ───────────────────────

def search_knowledge_base(query, top_k=None, **kwargs):
    """Search the wellness knowledge base using FAISS vector similarity.

    Returns relevant document chunks with sources and scores.
    """
    if top_k is None:
        top_k = RAG_TOP_K

    try:
        index, metadata = _load_faiss()
    except FileNotFoundError as e:
        logger.error(str(e))
        return {
            "results": [],
            "message": "Knowledge base index not available. Please try again later.",
        }

    query_vec = _get_query_embedding(query)
    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        if score < RAG_SIMILARITY_THRESHOLD:
            continue

        chunk = metadata["chunks"][idx]
        results.append({
            "text": chunk["text"],
            "title": chunk["title"],
            "category": chunk["category"],
            "source_file": chunk["filename"],
            "relevance_score": round(float(score), 4),
        })

    if not results:
        return {
            "results": [],
            "message": (
                "No sufficiently relevant information found in the knowledge base "
                "for this query. The bot should acknowledge this honestly rather "
                "than inventing information."
            ),
        }

    return {"results": results}


# ── Tool: create_goal ─────────────────────────────────

def create_goal(user_id, title, category, target_date=None, initial_progress=0, **kwargs):
    """Create a new wellness goal for the user."""
    try:
        goal = goal_service.create(
            user_id=user_id,
            title=title,
            category=category,
            target_date=target_date,
            initial_progress=initial_progress,
        )
        return {"goal": goal, "message": f"Goal '{title}' created successfully."}
    except ValueError as e:
        return {"error": str(e)}


# ── Tool: get_goals ───────────────────────────────────

def get_goals(user_id, status_filter="active", limit=5, **kwargs):
    """Retrieve the user's wellness goals."""
    try:
        goals = goal_service.list_for_user(
            user_id=user_id,
            status_filter=status_filter,
            limit=limit,
        )
        if not goals:
            return {
                "goals": [],
                "message": f"No {status_filter} goals found. The user might want to create one.",
            }
        return {"goals": goals, "count": len(goals)}
    except ValueError as e:
        return {"error": str(e)}


# ── Tool: update_goal ─────────────────────────────────

def update_goal(user_id, goal_id, progress_pct=None, status=None, update_notes=None, **kwargs):
    """Update an existing wellness goal."""
    try:
        goal = goal_service.update(
            user_id=user_id,
            goal_id=goal_id,
            progress_pct=progress_pct,
            status=status,
            notes=update_notes,
        )
        if goal is None:
            return {"error": f"Goal {goal_id} not found or you don't have access to it."}
        return {"goal": goal, "message": "Goal updated successfully."}
    except ValueError as e:
        return {"error": str(e)}
