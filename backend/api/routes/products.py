from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from models.schema import Product
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
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    # Sorting
    if sort == "price_asc":
        query = query.order_by(Product.current_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.current_price.desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else: # demand_desc
        query = query.order_by(Product.demand_velocity.desc())
        
    total = query.count()
    products = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "products": products,
        "total": total,
        "page": page,
        "limit": limit
    }
    
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
async def get_product_by_id(id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        return {"error": "not found"}
    return product


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
