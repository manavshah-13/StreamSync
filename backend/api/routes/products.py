from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from db.database import get_db
from models.schema import Product, PricingHistory
from db.redis_client import get_redis
from engine.recommendation_engine  import get_recommendations
from engine.personalisation_engine import rerank_by_session

router = APIRouter(tags=["Products"])


@router.get("/products")
@router.get("/v1/products")
async def get_products(
    category: str = Query(None),
    sort: str = Query("demand_desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(or_(Product.is_active == True, Product.is_active == None))
    
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
    
    serialized_products = []
    for product in products:
        base = product.base_price or 0.0
        current = product.current_price if product.current_price is not None else base
        price_change_pct = ((current - base) / base * 100.0) if base > 0.0 else 0.0

        # Fetch latest change reason
        latest_history = db.query(PricingHistory).filter(PricingHistory.product_id == product.id).order_by(PricingHistory.timestamp.desc()).first()
        change_reason = latest_history.change_reason if latest_history else "Price adjusted dynamically based on market demand velocity."

        specs = product.specs or {}
        stock_count = product.stock_count if getattr(product, 'stock_count', None) is not None else int(specs.get("stock_count", 50))
        is_trending = product.is_trending if getattr(product, 'is_trending', None) is not None else (bool(specs.get("is_trending", False)) or (product.demand_velocity or 0) > 30)
        is_active = product.is_active if getattr(product, 'is_active', None) is not None else bool(specs.get("is_active", True))

        serialized_products.append({
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "base_price": product.base_price,
            "original_price": product.base_price,
            "current_price": current,
            "price_change_percentage": round(price_change_pct, 2),
            "change_reason": change_reason,
            "rating": product.rating,
            "review_count": product.review_count,
            "demand_velocity": product.demand_velocity,
            "brand": product.brand,
            "description": product.description,
            "specs": product.specs,
            "image": product.image,
            "color": product.color,
            "material": product.material,
            "style": product.style,
            "tags": product.tags,
            "created_at": product.created_at,
            "is_active": is_active,
            "is_trending": is_trending,
            "stock_count": stock_count,
        })

    return {
        "products": serialized_products,
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
@router.get("/v1/products/{id}")
async def get_product_by_id(id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        return {"error": "not found"}

    # Calculate price change percentage
    base = product.base_price or 0.0
    current = product.current_price if product.current_price is not None else base
    price_change_pct = ((current - base) / base * 100.0) if base > 0.0 else 0.0

    specs = product.specs or {}
    stock_count = product.stock_count if getattr(product, 'stock_count', None) is not None else int(specs.get("stock_count", 50))
    is_trending = product.is_trending if getattr(product, 'is_trending', None) is not None else (bool(specs.get("is_trending", False)) or (product.demand_velocity or 0) > 30)
    is_active = product.is_active if getattr(product, 'is_active', None) is not None else bool(specs.get("is_active", True))

    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "base_price": product.base_price,
        "original_price": product.base_price,
        "current_price": current,
        "price_change_percentage": round(price_change_pct, 2),
        "rating": product.rating,
        "review_count": product.review_count,
        "demand_velocity": product.demand_velocity,
        "brand": product.brand,
        "description": product.description,
        "specs": product.specs,
        "image": product.image,
        "color": product.color,
        "material": product.material,
        "style": product.style,
        "tags": product.tags,
        "created_at": product.created_at,
        "is_active": is_active,
        "is_trending": is_trending,
        "stock_count": stock_count,
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
