"""
GET /api/ml/insights
=====================
Returns a unified ML health dashboard:
  - Revenue uplift top gainers / rollback hints
  - Fairness audit summary + recent alerts
  - Latency p50 / p95 / p99 per API route
  - Model warm-up status for each engine
  - Semantic search index stats
"""
from fastapi import APIRouter, Depends
from db.redis_client           import get_redis
from engine.revenue_uplift_model import get_top_uplift_products
from engine.fairness_audit       import get_audit_summary
from engine.latency_tracker      import tracker
from engine.semantic_search      import semantic_engine

router = APIRouter(prefix="/ml", tags=["ML Insights"])


@router.get("/insights")
async def get_ml_insights(redis=Depends(get_redis)):
    """Full ML health report — suitable for a developer dashboard."""

    # ── Revenue Uplift ─────────────────────────────────────────────────────────
    top_uplift = await get_top_uplift_products(redis, limit=5)

    # ── Fairness Audit ─────────────────────────────────────────────────────────
    fairness = await get_audit_summary(redis)

    # ── Latency Stats ──────────────────────────────────────────────────────────
    latency_all = tracker.get_stats()
    # Summarise key routes only
    KEY_ROUTES = ["/api/products", "/api/search", "/api/recommendations", "/api/metrics"]
    latency_summary = {
        route: latency_all[route]
        for route in KEY_ROUTES
        if route in latency_all
    }
    # Add overall p99 across all routes
    all_p99 = [v["p99"] for v in latency_all.values() if "p99" in v]
    overall_p99 = round(max(all_p99), 1) if all_p99 else 0.0

    # ── Model Warm-up Status ───────────────────────────────────────────────────
    # Proxy: check if at least some co-click data exists
    co_click_keys   = await redis.keys("co_clicks:*")
    session_keys    = await redis.keys("session:*:profile")
    uplift_keys     = await redis.keys("uplift:*:events")
    fairness_count  = await redis.llen("fairness_alerts")

    model_status = {
        "recommendation_engine":  "warm" if len(co_click_keys) >= 3  else "cold",
        "personalisation_engine": "warm" if len(session_keys)  >= 2  else "cold",
        "revenue_uplift_model":   "warm" if len(uplift_keys)   >= 1  else "cold",
        "fairness_audit":         "warm" if fairness_count      >= 0  else "cold",
        "pricing_model":          "warm",  # always active
        "semantic_search":        "warm" if semantic_engine._ready    else "cold",
    }

    # ── Semantic Search Index Stats ────────────────────────────────────────────
    search_stats = {
        "status":         "warm" if semantic_engine._ready else "cold",
        "indexed_products": len(semantic_engine._products),
        "unique_terms":     len(semantic_engine._idf),
    }

    return {
        "revenue_uplift": {
            "top_products": top_uplift,
        },
        "fairness_audit":  fairness,
        "latency": {
            "overall_p99_ms": overall_p99,
            "by_route":       latency_summary,
        },
        "model_status":    model_status,
        "semantic_search": search_stats,
    }
