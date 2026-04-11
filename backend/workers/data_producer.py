import time
import json
import random
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.redis_client import get_redis_sync

def run_simulation():
    client = get_redis_sync()
    stream_name = "ingestion_stream"
    
    print("Starting background traffic simulation to Redis Streams...")
    time.sleep(3) # Wait for consumer / setup
    
    while True:
        try:
            # Simulate a continuous stream of VIEW and CART signals
            num_events = random.randint(1, 15)
            
            for _ in range(num_events):
                prod_target = random.randint(1, 20)
                event_type = random.choice(["VIEW", "VIEW", "VIEW", "ADD_TO_CART"])
                
                payload = {
                    "type": event_type,
                    "productId": f"prod-{prod_target}",
                    "sessionId": f"sess_{random.randint(1000, 9999)}",
                    "ts": time.strftime("%H:%M:%S")
                }
                
                client.xadd(stream_name, {"payload": json.dumps(payload)})
                
            time.sleep(random.uniform(0.5, 2.0))
            
        except Exception as e:
            print(f"Producer error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_simulation()
