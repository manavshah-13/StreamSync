from fastapi import APIRouter, Depends
from db.redis_client import get_redis
from engine.recommender import get_similar_skus

router = APIRouter(tags=["Products"])

@router.get("/products")
async def get_products(redis=Depends(get_redis)):
    sku_keys = await redis.smembers("products:all")
    products = []
    for sku in sku_keys:
        prod = await redis.hgetall(f"product:{sku}")
        if prod:
            products.append({
                "id": prod.get("id"),
                "name": prod.get("name"),
                "category": prod.get("category"),
                "price": float(prod.get("current_price", 0)),
                "rating": float(prod.get("rating", 0)),
                "reviewCount": int(prod.get("reviewCount", 0)),
                "demandVelocity": int(prod.get("demandVelocity", 50)),
                "brand": prod.get("brand"),
                "image": prod.get("image", None)
            })
    products.sort(key=lambda x: x["name"])
    return {"products": products}

@router.get("/products/{id}")
async def get_product_by_id(id: str, redis=Depends(get_redis)):
    prod = await redis.hgetall(f"product:{id}")
    if not prod:
        return {"error": "not found"}
        
    import json
    specs = json.loads(prod.get("specs", "{}"))
    
    return {
        "id": prod.get("id"),
        "name": prod.get("name"),
        "category": prod.get("category"),
        "price": float(prod.get("current_price", 0)),
        "rating": float(prod.get("rating", 0)),
        "reviewCount": int(prod.get("reviewCount", 0)),
        "demandVelocity": int(prod.get("demandVelocity", 50)),
        "brand": prod.get("brand"),
        "description": prod.get("description"),
        "specs": specs,
        "image": prod.get("image", None)
    }

@router.get("/recommendations")
async def get_recommendation(redis=Depends(get_redis)):
    recs = get_similar_skus("prod-1", 4)
    products = []
    for sku in recs:
        prod = await redis.hgetall(f"product:{sku}")
        if prod:
            products.append({
                "id": prod.get("id"),
                "name": prod.get("name"),
                "category": prod.get("category"),
                "price": float(prod.get("current_price", 0)),
                "rating": float(prod.get("rating", 0)),
                "reviewCount": int(prod.get("reviewCount", 0)),
                "demandVelocity": int(prod.get("demandVelocity", 50)),
                "brand": prod.get("brand"),
                "image": prod.get("image", None)
            })
    return {"products": products}
