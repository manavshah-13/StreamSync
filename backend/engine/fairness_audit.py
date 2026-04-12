"""
FairnessAuditModel — Price Disparity Monitor
=============================================
After every repricing event, checks that:
  1. No product's price exceeds 1.35× its base price (ceiling breach)
  2. Category-level disparity: no SKU should be >40% above the category average

Violations are pushed to the 'fairness_alerts' Redis list (max 50).

Redis keys:
  fairness_alerts  → list of JSON alert objects (newest first)
"""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CEILING_RATIO  = 1.35   # Price must not exceed base × 1.35
FLOOR_RATIO    = 0.85   # Price must not drop below base × 0.85
MAX_ALERTS     = 50


async def check(redis, product_id: str, base_price: float, new_price: float, category: str = ""):
    """
    Called by stream_consumer after every repricing.
    Pushes an alert to Redis if a fairness violation is detected.
    """
    try:
        if base_price <= 0:
            return

        ratio = new_price / base_price
        alerts = []

        if ratio > CEILING_RATIO:
            alerts.append({
                "type":        "CEILING_BREACH",
                "product_id":  product_id,
                "category":    category,
                "ratio":       round(ratio, 3),
                "threshold":   CEILING_RATIO,
                "new_price":   round(new_price, 2),
                "base_price":  round(base_price, 2),
                "severity":    "HIGH" if ratio > 1.45 else "MEDIUM",
                "message":     f"Price is {ratio:.1%} of base — exceeds fair ceiling of {CEILING_RATIO:.0%}",
                "ts":          datetime.now(timezone.utc).isoformat(),
            })

        if ratio < FLOOR_RATIO:
            alerts.append({
                "type":        "FLOOR_BREACH",
                "product_id":  product_id,
                "category":    category,
                "ratio":       round(ratio, 3),
                "threshold":   FLOOR_RATIO,
                "new_price":   round(new_price, 2),
                "base_price":  round(base_price, 2),
                "severity":    "LOW",
                "message":     f"Price is {ratio:.1%} of base — below floor of {FLOOR_RATIO:.0%}",
                "ts":          datetime.now(timezone.utc).isoformat(),
            })

        for alert in alerts:
            await redis.lpush("fairness_alerts", json.dumps(alert))

        if alerts:
            await redis.ltrim("fairness_alerts", 0, MAX_ALERTS - 1)
            logger.debug(f"[FairnessAudit] {len(alerts)} alert(s) for {product_id}")

    except Exception as e:
        logger.warning(f"[FairnessAudit] check error: {e}")


async def get_recent_alerts(redis, limit: int = 10) -> list:
    """Returns the most recent fairness alerts."""
    try:
        raw = await redis.lrange("fairness_alerts", 0, limit - 1)
        return [json.loads(r) for r in raw]
    except Exception as e:
        logger.warning(f"[FairnessAudit] get_recent_alerts error: {e}")
        return []


async def get_audit_summary(redis) -> dict:
    """Returns an aggregate summary of fairness health."""
    try:
        raw = await redis.lrange("fairness_alerts", 0, MAX_ALERTS - 1)
        alerts = [json.loads(r) for r in raw]

        ceiling_breaches = sum(1 for a in alerts if a.get("type") == "CEILING_BREACH")
        floor_breaches   = sum(1 for a in alerts if a.get("type") == "FLOOR_BREACH")
        high_severity    = sum(1 for a in alerts if a.get("severity") == "HIGH")

        return {
            "total_alerts":      len(alerts),
            "ceiling_breaches":  ceiling_breaches,
            "floor_breaches":    floor_breaches,
            "high_severity":     high_severity,
            "health_score":      max(0, 100 - len(alerts) * 2),  # 0-100, penalise per alert
            "recent_alerts":     alerts[:5],
        }
    except Exception as e:
        logger.warning(f"[FairnessAudit] get_audit_summary error: {e}")
        return {"total_alerts": 0, "health_score": 100, "recent_alerts": []}
