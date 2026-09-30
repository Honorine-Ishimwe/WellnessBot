"""
Build the FAISS vector index from wellness knowledge documents.

Run once (or whenever documents change):
    python -m backend.tools.build_index
"""

import os
import json
import pickle
import re

import numpy as np

from openai import OpenAI

from backend.config import (
    KNOWLEDGE_DIR,
    FAISS_INDEX_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

_client = OpenAI()

FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "wellness.faiss")
METADATA_PATH = os.path.join(FAISS_INDEX_DIR, "wellness_metadata.pkl")


def load_documents():
    """Load all .md files from the knowledge directory."""
    docs = []
    for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Extract category from document metadata
        category = "other"
        cat_match = re.search(r"\*\*Category:\*\*\s*(\w+)", text)
        if cat_match:
            category = cat_match.group(1).lower()

        # Extract title from first heading
        title = filename.replace(".md", "").replace("_", " ").title()
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        docs.append({
            "filename": filename,
            "title": title,
            "category": category,
            "text": text,
        })
    return docs


def chunk_document(doc, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split a document into overlapping chunks."""
    text = doc["text"]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append({
                "text": chunk_text.strip(),
                "title": doc["title"],
                "category": doc["category"],
                "filename": doc["filename"],
                "chunk_index": len(chunks),
            })
        start += chunk_size - overlap
    return chunks


def get_embeddings(texts, model=EMBEDDING_MODEL):
    """Get embeddings for a list of texts from OpenAI."""
    response = _client.embeddings.create(
        input=texts,
        model=model,
    )
    return [item.embedding for item in response.data]


def build_index():
    """Build the FAISS index from all knowledge documents."""
    import faiss

    print("[Index] Loading documents...")
    docs = load_documents()
    print(f"[Index] Found {len(docs)} documents")

    # Chunk all documents
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"[Index] Created {len(all_chunks)} chunks")

    # Get embeddings in batches of 100
    print("[Index] Generating embeddings...")
    all_embeddings = []
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch_texts = [c["text"] for c in all_chunks[i : i + batch_size]]
        batch_embeddings = get_embeddings(batch_texts)
        all_embeddings.extend(batch_embeddings)
        print(f"[Index] Embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")

    # Build FAISS index
    embeddings_matrix = np.array(all_embeddings, dtype="float32")
    dimension = embeddings_matrix.shape[1]

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings_matrix)

    index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine after normalization)
    index.add(embeddings_matrix)

    # Save index and metadata
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)

    metadata = {
        "chunks": all_chunks,
        "dimension": dimension,
        "num_chunks": len(all_chunks),
        "num_documents": len(docs),
        "embedding_model": EMBEDDING_MODEL,
    }
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"[Index] FAISS index saved to {FAISS_INDEX_PATH}")
    print(f"[Index] Metadata saved to {METADATA_PATH}")
    print(f"[Index] Index contains {index.ntotal} vectors of dimension {dimension}")

    return index, metadata


if __name__ == "__main__":
    build_index()
