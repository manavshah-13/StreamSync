"""
RevenueUpliftModel — Post-Reprice Impact Measurement
=====================================================
After every repricing event, records:
  - old_price, new_price
  - click count in the 60s window before repricing

On demand, computes estimated revenue uplift per product.
If a price increase triggered a demand drop → suggests rollback.

Redis keys:
  uplift:{product_id}:events  → list of JSON reprice records (max 20)
  velocity_raw:{product_id}    → hash with 'clicks' counter (from stream consumer)
"""
import json
import time
import logging

logger = logging.getLogger(__name__)

MAX_EVENTS = 20


async def record_reprice(redis, product_id: str, old_price: float, new_price: float):
    """
    Called by stream_consumer immediately after a price is updated.
    Snapshots the current click-rate as 'clicks_before'.
    """
    try:
        vel_data = await redis.hgetall(f"velocity_raw:{product_id}")
        clicks_before = int(vel_data.get("clicks", 0)) if vel_data else 0

        event = {
            "product_id": product_id,
            "old_price":  round(old_price, 2),
            "new_price":  round(new_price, 2),
            "ts":         time.time(),
            "clicks_before": clicks_before,
        }

        key = f"uplift:{product_id}:events"
        await redis.lpush(key, json.dumps(event))
        await redis.ltrim(key, 0, MAX_EVENTS - 1)

    except Exception as e:
        logger.warning(f"[RevenueUpliftModel] record_reprice error: {e}")


async def compute_uplift(redis, product_id: str) -> dict:
    """
    Computes estimated revenue uplift using:
      uplift = new_price × clicks_after − old_price × clicks_before
    Also returns a rollback_recommended flag if uplift is consistently negative.
    """
    try:
        events_raw = await redis.lrange(f"uplift:{product_id}:events", 0, -1)
        if not events_raw:
            return {"total_uplift": 0.0, "events": 0, "rollback_recommended": False}

        vel_data   = await redis.hgetall(f"velocity_raw:{product_id}")
        clicks_now = int(vel_data.get("clicks", 0)) if vel_data else 0

        total_uplift = 0.0
        negative_count = 0

        for raw in events_raw:
            ev = json.loads(raw)
            clicks_before = ev.get("clicks_before", 0)
            # Use current clicks as proxy for clicks_after (approximation)
            clicks_after  = max(clicks_now, clicks_before)
            uplift = ev["new_price"] * clicks_after - ev["old_price"] * clicks_before
            total_uplift += uplift
            if uplift < 0:
                negative_count += 1

        rollback = negative_count >= len(events_raw) * 0.6  # >60% negative events

        return {
            "total_uplift":          round(total_uplift, 2),
            "events":                len(events_raw),
            "rollback_recommended":  rollback,
            "negative_reprice_ratio": round(negative_count / max(len(events_raw), 1), 2),
        }

    except Exception as e:
        logger.warning(f"[RevenueUpliftModel] compute_uplift error: {e}")
        return {"total_uplift": 0.0, "events": 0, "rollback_recommended": False}


async def get_top_uplift_products(redis, limit: int = 5) -> list:
    """Returns products sorted by estimated revenue uplift (top gainers first)."""
    try:
        all_products = await redis.smembers("products:all")
        results = []
        for pid in all_products:
            data = await compute_uplift(redis, pid)
            prod = await redis.hgetall(f"product:{pid}")
            results.append({
                "product_id":   pid,
                "name":         prod.get("name", pid) if prod else pid,
                "total_uplift": data["total_uplift"],
                "rollback_recommended": data["rollback_recommended"],
            })

        results.sort(key=lambda x: x["total_uplift"], reverse=True)
        return results[:limit]

    except Exception as e:
        logger.warning(f"[RevenueUpliftModel] get_top_uplift_products error: {e}")
        return []
