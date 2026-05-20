import os
import json
import faiss
import numpy as np
from django.conf import settings
from .models import DocumentChunk

BASE_DIR = settings.BASE_DIR
FAISS_DIR = os.path.join(BASE_DIR, "faiss_data")
INDEX_FILE = os.path.join(FAISS_DIR, "documents.index")
MAPPING_FILE = os.path.join(FAISS_DIR, "documents_mapping.json")


def ensure_faiss_dir():
    os.makedirs(FAISS_DIR, exist_ok=True)


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    return vectors / norms


def rebuild_faiss_index():
    """
    از تمام chunkهایی که embedding دارند، index می‌سازد.
    """
    ensure_faiss_dir()

    chunks = list(
        DocumentChunk.objects
        .exclude(embedding=None)
        .select_related("document")
        .order_by("id")
    )

    if not chunks:
        if os.path.exists(INDEX_FILE):
            os.remove(INDEX_FILE)
        if os.path.exists(MAPPING_FILE):
            os.remove(MAPPING_FILE)
        return {
            "status": "empty",
            "count": 0
        }

    embeddings = []
    mapping = []

    for chunk in chunks:
        emb = chunk.embedding
        if not emb:
            continue
        embeddings.append(emb)
        mapping.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index
        })

    if not embeddings:
        return {
            "status": "empty",
            "count": 0
        }

    vectors = np.array(embeddings, dtype="float32")
    vectors = l2_normalize(vectors)

    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine-like after normalization
    index.add(vectors)

    faiss.write_index(index, INDEX_FILE)
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    return {
        "status": "ok",
        "count": len(mapping),
        "dimension": dimension
    }


def load_faiss_index():
    if not os.path.exists(INDEX_FILE) or not os.path.exists(MAPPING_FILE):
        return None, None

    index = faiss.read_index(INDEX_FILE)
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    return index, mapping


def search_faiss(query_embedding, k=5):
    """
    query_embedding: list[float]
    خروجی: لیست chunkها به ترتیب relevance
    """
    index, mapping = load_faiss_index()
    if index is None or mapping is None:
        rebuild_faiss_index()
        index, mapping = load_faiss_index()
        if index is None:
            return []

    query_vector = np.array([query_embedding], dtype="float32")
    query_vector = l2_normalize(query_vector)

    distances, indices = index.search(query_vector, k)

    selected_chunk_ids = []
    for idx in indices[0]:
        if idx == -1:
            continue
        if idx < len(mapping):
            selected_chunk_ids.append(mapping[idx]["chunk_id"])

    if not selected_chunk_ids:
        return []

    chunk_map = {
        chunk.id: chunk
        for chunk in DocumentChunk.objects
        .filter(id__in=selected_chunk_ids)
        .select_related("document")
    }

    results = []
    for chunk_id in selected_chunk_ids:
        chunk = chunk_map.get(chunk_id)
        if chunk:
            results.append(chunk)

    return results
