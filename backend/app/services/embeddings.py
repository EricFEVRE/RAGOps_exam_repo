import httpx
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.utils.hashing import md5_hash
from app.utils.cache import get_json, set_json

_CACHE_TTL = 3600  # seconds
_TEI_BATCH_SIZE = 32  # TEI max batch size

# TEI is called directly to avoid LiteLLM injecting encoding_format,
# which TEI does not support despite advertising an OpenAI-compatible API.
_TEI_URL = getattr(settings, "TEI_URL", "http://tei-embeddings:80")


async def _request_embeddings(texts: List[str]) -> Optional[List[dict]]:
    """Call TEI in batches of _TEI_BATCH_SIZE to respect server limits."""
    all_data = []
    for i in range(0, len(texts), _TEI_BATCH_SIZE):
        batch = texts[i: i + _TEI_BATCH_SIZE]
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{_TEI_URL}/v1/embeddings",
                # NOTE: do NOT pass encoding_format — TEI rejects it
                json={"model": "local-embeddings", "input": batch},
                headers={"Content-Type": "application/json"},
            )
        if r.status_code != 200:
            logger.error(f"Embedding request failed: {r.status_code} - {r.text}")
            return None
        batch_data = r.json().get("data", [])
        # Re-index so positions are relative to the full list
        for item in batch_data:
            item["index"] = len(all_data) + item.get("index", 0)
        all_data.extend(batch_data)
    return all_data


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate sentence embeddings via TEI directly (bypasses LiteLLM proxy),
    with Redis cache. Handles TEI batch size limit automatically.
    """
    results: List[Optional[List[float]]] = [None] * len(texts)
    uncached, idxs = [], []

    # 1) cache lookups
    for i, t in enumerate(texts):
        key = f"embedding:{md5_hash(t)}"
        cached_vec = get_json(key)
        if cached_vec is not None:
            results[i] = cached_vec
        else:
            uncached.append(t)
            idxs.append(i)

    # 2) remote call if needed (batched internally)
    if uncached:
        data = await _request_embeddings(uncached)
        if data is None:
            # Fail closed: return only cached results
            return [v for v in results if v is not None]

        for i, emb in zip(idxs, data):
            vec = emb.get("embedding", emb)
            if isinstance(vec, dict) and "default" in vec:
                vec = vec["default"]
            results[i] = vec
            set_json(f"embedding:{md5_hash(texts[i])}", vec, _CACHE_TTL)

    # 3) flatten and filter
    return [v for v in results if v is not None]