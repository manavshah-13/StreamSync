import asyncio
import json
import logging
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.redis_client import get_redis_async
from engine.pricing_model import calculate_new_price

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_consumer():
    r = get_redis_async()
    stream_name = "ingestion_stream"
    group_name = "pricing_workers"
    
    try:
        await r.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        logger.info(f"Created consumer group {group_name}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            logger.error(f"Error creating group: {e}")
            
    logger.info("Starting stream consumer loop...")
    last_id = ">"
    
    while True:
        try:
            messages = await r.xreadgroup(group_name, "worker-1", {stream_name: last_id}, count=50, block=2000)
            if not messages:
                continue
                
            for stream, entries in messages:
                for msg_id, msg_data in entries:
                    try:
                        payload = msg_data.get("payload")
                        if payload:
                            event = json.loads(payload)
                            product_id = event.get("productId")
                            
                            if product_id:
                                # 1. Update rolling metric
                                await r.hincrby(f"velocity_raw:{product_id}", "clicks", 1)
                                
                                # 2. Grab current data
                                prod_key = f"product:{product_id}"
                                prod = await r.hgetall(prod_key)
                                
                                if prod:
                                    velocity = int(prod.get("demandVelocity", 50))
                                    base_price = float(prod.get("base_price", 19.99))
                                    current_price = float(prod.get("current_price", 19.99))
                                    
                                    # Simulate velocity shift (decay or spike)
                                    new_velocity = min(100, velocity + 2) 
                                    
                                    # 3. Dynamic Repricing Logic
                                    if new_velocity > 75:
                                        new_price = calculate_new_price(base_price, current_price, new_velocity)
                                        if new_price != current_price:
                                            await r.hset(prod_key, "current_price", new_price)
                                            await r.hset(prod_key, "demandVelocity", new_velocity)
                                            
                                            evt = {
                                                "id": str(msg_id.split("-")[0]),
                                                "sku": product_id,
                                                "oldPrice": current_price,
                                                "newPrice": new_price,
                                                "reason": f"Demand spike +{new_velocity}% velocity",
                                                "ts": event.get("ts", "")
                                            }
                                            await r.lpush("repricing_events", json.dumps(evt))
                                            await r.ltrim("repricing_events", 0, 99)
                                            logger.info(f"Repriced {product_id}: {current_price} -> {new_price}")
                                    else:
                                        await r.hset(prod_key, "demandVelocity", new_velocity)
                        
                        await r.xack(stream_name, group_name, msg_id)
                    except Exception as e:
                        logger.error(f"Failed to process message {msg_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_consumer())
