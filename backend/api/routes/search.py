"""
GET /api/search?q=<query>&limit=<n>
=====================================
Semantic search endpoint backed by SemanticSearchEngine.
Returns products sorted by relevance with query_parsed breakdown.

Example:
  GET /api/search?q=green+yoga+mat&limit=5
  → {products: [...], query_parsed: {colors: ['green'], category: 'Sports', ...}, total: 3}
"""
from fastapi import APIRouter, Query
from engine.semantic_search import semantic_engine

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search_products(
    q:     str = Query(..., min_length=1, description="Natural language search query"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Semantic search — understands colour, material, style and product-type hints.
    Falls back gracefully if the index is still warming up (returns status='cold').
    """
    result = semantic_engine.query(q.strip(), limit=limit)
    return result
