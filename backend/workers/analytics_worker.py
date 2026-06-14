import asyncio
import logging
import sys
import os
from typing import Optional
import redis.asyncio as aioredis

# Add parent directory to module search path to resolve relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.redis_client import get_redis_async
from analytics.session_profiles import update_user_affinity, record_session_interaction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workers.analytics_worker")

def safe_str(val) -> str:
    """
    Decodes byte strings safely or converts values to clean strings.
    """
    if isinstance(val, bytes):
        return val.decode("utf-8")
    return str(val) if val is not None else ""

async def process_single_event(r: aioredis.Redis, msg_id: str, msg_data: dict, stream_name: str, group_name: str) -> None:
    """
    Processes a single stream event: resolves SKU category, updates user affinity,
    updates rolling session history, and sends XACK.
    """
    try:
        user_id = safe_str(msg_data.get("user_id"))
        session_id = safe_str(msg_data.get("session_id"))
        event_type = safe_str(msg_data.get("event_type"))
        sku = safe_str(msg_data.get("sku"))

        if not sku or not user_id:
            logger.warning(f"[Worker] Skipping invalid event message {msg_id}: missing user_id or sku")
            await r.xack(stream_name, group_name, msg_id)
            return

        # Resolve the category for the SKU from the product hash key
        category_id = await r.hget(f"product:{sku}", "category")
        category_id = safe_str(category_id) if category_id else "General"

        # Update affinity score and session history concurrently/pipeline
        await update_user_affinity(user_id, event_type, category_id, redis_client=r)
        await record_session_interaction(session_id, sku, redis_client=r)

        # Acknowledge successful processing
        await r.xack(stream_name, group_name, msg_id)
        logger.debug(f"[Worker] Successfully processed and ACKed event {msg_id} for User {user_id}")

    except Exception as e:
        logger.error(f"[Worker] Failed to process message {msg_id}: {e}", exc_info=True)
        # We don't ACK failed messages so they remain in the pending entry list (PEL) for retry

async def run_worker(redis_client: Optional[aioredis.Redis] = None) -> None:
    """
    Main worker execution loop that subscribes to the 'stream:user_events' Redis stream 
    via consumer group 'analytics_workers'.
    """
    # Use provided client or establish connection pool
    r = redis_client if redis_client else get_redis_async()

    stream_name = "stream:user_events"
    group_name = "analytics_workers"
    consumer_name = "analytics-worker-1"

    # Register Consumer Group
    try:
        # Create group starting at '0' to read historical events or mkstream if it doesn't exist
        await r.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        logger.info(f"[Worker] Created consumer group {group_name} on stream {stream_name}")
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            logger.error(f"[Worker] Consumer group create error: {e}")
        else:
            logger.info(f"[Worker] Consumer group {group_name} already exists.")

    logger.info("[Worker] Analytics stream consumer loop started.")

    while True:
        try:
            # If using FakeRedis for testing, use a very low block time to avoid blocking the event loop
            is_fake = "Fake" in type(r).__name__
            block_ms = 10 if is_fake else 2000

            messages = await r.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=20,
                block=block_ms
            )

            if not messages:
                # Yield control to the event loop to prevent tight CPU looping
                await asyncio.sleep(0.01)
                continue

            for stream, entries in messages:
                for msg_id, msg_data in entries:
                    await process_single_event(r, msg_id, msg_data, stream_name, group_name)

        except aioredis.ConnectionError as ce:
            logger.error(f"[Worker] Redis connection lost: {ce}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"[Worker] Error in analytics worker main loop: {e}", exc_info=True)
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("[Worker] Analytics worker stopped by user.")
