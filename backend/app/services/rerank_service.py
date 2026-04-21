import httpx
import numpy as np
from typing import Dict, Any, List
from app.models.rerank import RerankRequest
from app.services.search_service import search_chunks
from app.core.config import settings

_TEI_URL = getattr(settings, "TEI_URL", "http://tei-embeddings:80")
_TEI_BATCH_SIZE = 32

async def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Call TEI directly (no LiteLLM) in batches to avoid encoding_format issues."""
    all_embeddings = []
    for i in range(0, len(texts), _TEI_BATCH_SIZE):
        batch = texts[i: i + _TEI_BATCH_SIZE]
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{_TEI_URL}/v1/embeddings",
                json={"model": "local-embeddings", "input": batch},
                headers={"Content-Type": "application/json"},
            )
        r.raise_for_status()
        batch_data = r.json().get("data", [])
        all_embeddings.extend([item["embedding"] for item in batch_data])
    return all_embeddings


def _cosine_sim(a: List[float], b: List[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(np.dot(a_arr, b_arr) / denom) if denom > 0 else 0.0


async def search_with_reranking(req: RerankRequest) -> Dict[str, Any]:
    base_results = await search_chunks(req.query, req.k, use_embeddings=True)
    hits = base_results.get("hits", [])
    if not hits:
        return {
            "query": req.query,
            "chunks": [],
            "rerank_scores": [],
            "total_chunks_found": 0,
            "search_method": "hybrid+rerank",
        }

    documents = [chunk["content"] for chunk in hits]

    # Embed query and documents via TEI directly
    query_embeddings = await _embed_texts([req.query])
    doc_embeddings = await _embed_texts(documents)

    query_vec = query_embeddings[0]
    scores = [_cosine_sim(query_vec, doc_vec) for doc_vec in doc_embeddings]

    scored_chunks = sorted(
        zip(hits, scores), key=lambda x: x[1], reverse=True
    )

    return {
        "query": req.query,
        "chunks": [c for c, _ in scored_chunks],
        "rerank_scores": [s for _, s in scored_chunks],
        "total_chunks_found": base_results.get("total", len(hits)),
        "search_method": "hybrid+rerank",
    }