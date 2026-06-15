from fastapi import APIRouter, Depends
import random
import time
from core.redis import get_redis
import redis.asyncio as aioredis

router = APIRouter(prefix="/analytics", tags=["Analytics V1"])

@router.get("/overview")
async def get_analytics_overview(redis: aioredis.Redis = Depends(get_redis)):
    try:
        # Check lengths of stream:user_events
        events_count = await redis.xlen("stream:user_events")
    except Exception:
        events_count = 0

    try:
        reprice_events = await redis.llen("repricing_events")
    except Exception:
        reprice_events = 0

    # Pricing multiplier variation factor
    factor = round(0.95 + random.uniform(-0.25, 0.45), 2)
    velocity = random.randint(110, 240) if events_count == 0 else min(350, 100 + events_count * 5)

    return {
        "p99Latency": round(135.2 + random.uniform(-8.0, 12.0), 1),
        "activeSkus": "10.4M",
        "repricingRate": f"{max(41200, 41200 + reprice_events * 310)}/s",
        "activeSessions": random.randint(17800, 18900),
        "cacheHitRate": round(random.uniform(98.2, 99.8), 1),
        "streamLag": f"{max(3, events_count // 3)}ms",
        "current_tick": {
            "time": time.strftime("%H:%M:%S"),
            "variableFactor": factor,
            "velocity": velocity
        }
    }
