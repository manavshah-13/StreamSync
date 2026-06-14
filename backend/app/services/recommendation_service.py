import logging
import numpy as np
from typing import List
from analytics.session_profiles import get_active_session_history
from app.core.lifecycle import PRODUCT_EMBEDDING_CACHE
from models.schema import Product
from app.ml.indexer import build_product_text_blob
from app.ml.embedder import ProductEmbedder

logger = logging.getLogger(__name__)

async def compute_active_session_vector(session_id: str, db_session) -> List[float]:
    """
    Computes a composite, time-decayed session profile embedding vector for the user.
    - Retrieves the last 5 unique product interaction SKUs from Redis.
    - Fetches the vector embeddings from the in-memory cache or DB/model fallback.
    - Applies exponential time-decay weight.
    - Blends and normalizes. Falls back to a zero vector if session is empty.
    """
    try:
        # Retrieve the last 5 unique product SKUs from Redis
        raw_skus = await get_active_session_history(session_id)
        # Decode bytes keys if Redis client returned them as bytes
        skus = [
            sku.decode("utf-8") if isinstance(sku, bytes) else sku
            for sku in raw_skus
        ]
    except Exception as e:
        logger.error(f"Failed to fetch active session history for session {session_id}: {e}")
        skus = []

    if not skus:
        return [0.0] * 384

    vectors = []
    embedder = None

    for sku in skus:
        if not sku:
            continue
            
        # Try retrieving from the global startup memory cache
        vector = PRODUCT_EMBEDDING_CACHE.get(sku)
        if vector is not None:
            vectors.append(vector)
            continue

        # Fallback to database lookup
        try:
            product = db_session.query(Product).filter(Product.id == sku).first()
            if product:
                # Reconstruct text blob and compute embedding dynamically
                text_blob = build_product_text_blob(
                    name=product.name,
                    category=product.category,
                    description=product.description
                )
                if not embedder:
                    embedder = ProductEmbedder()
                vector = embedder.get_embedding(text_blob)
                
                # Cache it to prevent redundant DB calls or ML inference
                PRODUCT_EMBEDDING_CACHE[sku] = vector
                vectors.append(vector)
        except Exception as ex:
            logger.warning(f"Could not load fallback vector for product {sku}: {ex}")
            continue

    if not vectors:
        return [0.0] * 384

    # Apply exponential time-decay weight (decay_factor = 0.8)
    # Most recent SKU (index 0) has weight 1.0, next is 0.8, 0.64, etc.
    decay_factor = 0.8
    composite = np.zeros(384)

    for i, vec in enumerate(vectors):
        weight = decay_factor ** i
        composite += weight * np.array(vec, dtype=float)

    # Normalize the final composite vector
    norm = np.linalg.norm(composite)
    if norm > 0.0:
        composite = composite / norm
    else:
        composite = np.zeros(384)

    return composite.tolist()
