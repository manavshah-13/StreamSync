import asyncio
import json
import logging
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.redis_client import get_redis_async
from engine.pricing_model       import calculate_new_price, calculate_confidence
from engine.recommendation_engine   import record_click   as rec_record_click
from engine.personalisation_engine  import update_session as pers_update_session
from engine.revenue_uplift_model    import record_reprice as uplift_record_reprice
from engine.fairness_audit          import check          as fairness_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_consumer():
    r = get_redis_async()
    stream_name = "ingestion_stream"
    group_name  = "pricing_workers"

    try:
        await r.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        logger.info(f"[Consumer] Created group {group_name}")
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            logger.error(f"[Consumer] Group create error: {e}")

    logger.info("[Consumer] Stream consumer loop started.")

    while True:
        try:
            messages = await r.xreadgroup(
                group_name, "worker-1",
                {stream_name: ">"},
                count=50, block=2000,
            )
            if not messages:
                continue

            for stream, entries in messages:
                for msg_id, msg_data in entries:
                    try:
                        payload = msg_data.get("payload")
                        if not payload:
                            await r.xack(stream_name, group_name, msg_id)
                            continue

                        event      = json.loads(payload)
                        product_id = event.get("productId")
                        session_id = event.get("sessionId", "anon")
                        event_type = event.get("type", "VIEW")

                        if not product_id:
                            await r.xack(stream_name, group_name, msg_id)
                            continue

                        # ── 1. Raw click counter ───────────────────────────────
                        await r.hincrby(f"velocity_raw:{product_id}", "clicks", 1)

                        # ── 2. Recommendation Engine ───────────────────────────
                        await rec_record_click(r, product_id, session_id)

                        # ── 3. Personalisation Engine ──────────────────────────
                        await pers_update_session(r, session_id, product_id, event_type)

                        # ── 4. Dynamic Repricing ───────────────────────────────
                        prod_key = f"product:{product_id}"
                        prod     = await r.hgetall(prod_key)

                        if prod:
                            velocity      = int(prod.get("demandVelocity", 50))
                            base_price    = float(prod.get("base_price", 19.99))
                            current_price = float(prod.get("current_price", 19.99))
                            category      = prod.get("category", "")

                            # Get click rate for model input
                            vel_data   = await r.hgetall(f"velocity_raw:{product_id}")
                            click_rate = int(vel_data.get("clicks", 0)) if vel_data else 0

                            # Simulate velocity shift (incremental demand pressure)
                            new_velocity = min(100, velocity + 2)

                            # Only reprice on demand spikes
                            if new_velocity > 75:
                                new_price  = calculate_new_price(base_price, current_price, new_velocity, click_rate)
                                confidence = calculate_confidence(new_velocity, click_rate)

                                if new_price != current_price:
                                    await r.hset(prod_key, "current_price", new_price)
                                    await r.hset(prod_key, "demandVelocity", new_velocity)

                                    # ── 5. Revenue Uplift Model ────────────────
                                    await uplift_record_reprice(r, product_id, current_price, new_price)

                                    # ── 6. Fairness Audit ──────────────────────
                                    await fairness_check(r, product_id, base_price, new_price, category)

                                    # Log repricing event
                                    evt = {
                                        "id":         str(msg_id.split("-")[0]) if "-" in str(msg_id) else str(msg_id),
                                        "sku":        product_id,
                                        "oldPrice":   current_price,
                                        "newPrice":   new_price,
                                        "reason":     f"Demand spike +{new_velocity}% velocity",
                                        "confidence": confidence,
                                        "ts":         event.get("ts", ""),
                                    }
                                    await r.lpush("repricing_events", json.dumps(evt))
                                    await r.ltrim("repricing_events", 0, 99)
                                    logger.info(
                                        f"[Consumer] Repriced {product_id}: "
                                        f"{current_price:.0f} → {new_price:.0f}  "
                                        f"(conf={confidence:.2f})"
                                    )
                            else:
                                await r.hset(prod_key, "demandVelocity", new_velocity)

                        await r.xack(stream_name, group_name, msg_id)

                    except Exception as e:
                        logger.error(f"[Consumer] Failed to process {msg_id}: {e}")

        except Exception as e:
            logger.error(f"[Consumer] Loop error: {e}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run_consumer())
