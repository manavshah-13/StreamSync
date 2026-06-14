import logging
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from db.database import get_db
from models.schema import Product
from app.services.recommendation_service import compute_active_session_vector
from app.ml.similarity import rank_products_by_similarity
from app.core.lifecycle import PRODUCT_EMBEDDING_CACHE
from core.redis import redis_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/personalized")
async def get_personalized_recommendations(
    session_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="x-session-id"),
    x_user_id: Optional[str] = Header(None, alias="x-user-id"),
    db: Session = Depends(get_db)
):
    """
    GET /api/v1/recommendations/personalized
    Returns personalized product recommendations based on:
    1. Active session similarity search (if session vector has active history).
    2. User category affinity scores from Redis (as a warm fallback for returning users).
    3. Global trending products sorted by demand velocity (as a cold fallback).
    """
    final_session_id = session_id or x_session_id
    final_user_id = user_id or x_user_id

    # 1. Compute composite session vector
    session_vector = []
    if final_session_id:
        session_vector = await compute_active_session_vector(final_session_id, db)

    # Check if vector is populated (at least one non-zero component)
    is_vector_populated = any(v != 0.0 for v in session_vector)
    recommended_ids: List[Any] = []
    recommender_type = "cold_start_trending"

    # 2. Similarity search logic
    if is_vector_populated:
        recommended_ids = rank_products_by_similarity(
            user_session_vector=session_vector,
            product_catalog_vectors=PRODUCT_EMBEDDING_CACHE,
            limit=5
        )
        if recommended_ids:
            recommender_type = "vector_similarity"

    # 3. Redis category affinity fallback (warm-start)
    if not recommended_ids and final_user_id:
        category_affinity = None
        try:
            client = redis_service.get_client()
            affinities = await client.zrevrange(f"user:affinity:{final_user_id}", 0, 0)
            if affinities:
                category_affinity = affinities[0].decode("utf-8") if isinstance(affinities[0], bytes) else affinities[0]
        except Exception as e:
            logger.warning(f"Error querying Redis category affinity for user {final_user_id}: {e}")

        if category_affinity:
            products = db.query(Product).filter(
                Product.category == category_affinity
            ).order_by(Product.demand_velocity.desc()).limit(5).all()
            recommended_ids = [p.id for p in products]
            if recommended_ids:
                recommender_type = "category_affinity"

    # 4. Default global trending fallback (cold-start)
    if not recommended_ids:
        products = db.query(Product).order_by(
            Product.demand_velocity.desc()
        ).limit(5).all()
        recommended_ids = [p.id for p in products]
        recommender_type = "global_trending"

    # Hydrate products maintaining rank order
    if not recommended_ids:
        return {"products": [], "recommender": recommender_type}

    db_products = db.query(Product).filter(Product.id.in_(recommended_ids)).all()
    product_map = {p.id: p for p in db_products}

    hydrated_products = []
    for pid in recommended_ids:
        prod = product_map.get(pid)
        if prod:
            hydrated_products.append({
                "id": prod.id,
                "name": prod.name,
                "current_price": prod.current_price if prod.current_price is not None else (prod.base_price or 0.0),
                "image": prod.image,
                "description": prod.description
            })

    return {"products": hydrated_products, "recommender": recommender_type}
