import sys
import os
import asyncio
import threading
import uvicorn
from contextlib import asynccontextmanager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.mock_db          import generate_mock_products
from db.redis_client     import get_redis_sync
from workers.stream_consumer import run_consumer
from workers.data_producer   import run_simulation
from engine.semantic_search  import semantic_engine
from main import app


@asynccontextmanager
async def lifespan(fastapi_app):
    print("====================================")
    print("[INIT] Loading In-Memory FakeRedis Backend")
    generate_mock_products()

    print("[INIT] Building Semantic Search Index…")
    redis_sync = get_redis_sync()
    semantic_engine.build_index_from_redis_sync(redis_sync)

    print("[INIT] Starting AI Stream Consumer")
    def start_consumer():
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(run_consumer())

    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()

    print("[INIT] Starting Session-Aware Traffic Simulator")
    def start_producer():
        asyncio.set_event_loop(asyncio.new_event_loop())
        run_simulation()

    producer_thread = threading.Thread(target=start_producer, daemon=True)
    producer_thread.start()
    print("====================================")
    yield


app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
