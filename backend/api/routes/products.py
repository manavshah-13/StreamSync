from fastapi import APIRouter, Depends, Query
from db.redis_client import get_redis
from engine.recommendation_engine  import get_recommendations
from engine.personalisation_engine import rerank_by_session

router = APIRouter(tags=["Products"])


@router.get("/products")
async def get_products(
    category: str = Query(None),
    sort: str = Query("demand_desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    redis=Depends(get_redis)
):
    sku_keys = await redis.smembers("products:all")
    products = []
    for sku in sku_keys:
        prod = await redis.hgetall(f"product:{sku}")
        if prod:
            # Filter by category if specified
            if category and prod.get("category") != category:
                continue

            products.append({
                "id":            prod.get("id"),
                "name":          prod.get("name"),
                "category":      prod.get("category"),
                "price":         float(prod.get("current_price", 0)),
                "rating":        float(prod.get("rating", 0)),
                "reviewCount":   int(prod.get("reviewCount", 0)),
                "demandVelocity": int(prod.get("demandVelocity", 50)),
                "brand":         prod.get("brand"),
                "image":         prod.get("image", None),
                "color":         prod.get("color", ""),
                "material":      prod.get("material", ""),
                "style":         prod.get("style", ""),
                "tags":          prod.get("tags", ""),
            })
    
    # Sorting logic
    if sort == "price_asc":
        products.sort(key=lambda x: x["price"])
    elif sort == "price_desc":
        products.sort(key=lambda x: x["price"], reverse=True)
    elif sort == "newest":
        products.sort(key=lambda x: x["name"])
    else: # demand_desc
        products.sort(key=lambda x: x["demandVelocity"], reverse=True)

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = products[start:end]

    return {
        "products": paginated,
        "total": len(products),
        "page": page,
        "limit": limit
    }


@router.get("/products/{id}")
async def get_product_by_id(id: str, redis=Depends(get_redis)):
    prod = await redis.hgetall(f"product:{id}")
    if not prod:
        return {"error": "not found"}

    import json
    specs = json.loads(prod.get("specs", "{}"))

    return {
        "id":            prod.get("id"),
        "name":          prod.get("name"),
        "category":      prod.get("category"),
        "price":         float(prod.get("current_price", 0)),
        "rating":        float(prod.get("rating", 0)),
        "reviewCount":   int(prod.get("reviewCount", 0)),
        "demandVelocity": int(prod.get("demandVelocity", 50)),
        "brand":         prod.get("brand"),
        "description":   prod.get("description"),
        "specs":         specs,
        "image":         prod.get("image", None),
        "color":         prod.get("color", ""),
        "material":      prod.get("material", ""),
        "style":         prod.get("style", ""),
        "tags":          prod.get("tags", ""),
    }


@router.get("/recommendations")
async def get_recommendation(
    product_id: str = Query(default="prod-1"),
    session_id: str = Query(default="anon"),
    limit:      int = Query(default=4, ge=1, le=12),
    redis=Depends(get_redis),
):
    """
    Personalised recommendations:
    1. Fetch co-click based recs for product_id
    2. Re-rank by session interest profile
    """
    rec_ids = await get_recommendations(redis, product_id, session_id, limit)
    rec_ids = await rerank_by_session(redis, session_id, rec_ids)

    products = []
    for sku in rec_ids:
        prod = await redis.hgetall(f"product:{sku}")
        if prod:
            products.append({
                "id":            prod.get("id"),
                "name":          prod.get("name"),
                "category":      prod.get("category"),
                "price":         float(prod.get("current_price", 0)),
                "rating":        float(prod.get("rating", 0)),
                "reviewCount":   int(prod.get("reviewCount", 0)),
                "demandVelocity": int(prod.get("demandVelocity", 50)),
                "brand":         prod.get("brand"),
                "image":         prod.get("image", None),
            })
    return {"products": products}
