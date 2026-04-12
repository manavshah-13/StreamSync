import time
import json
import random
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.redis_client import get_redis_sync

# Category → typical product IDs (rough mapping for session locality)
CATEGORY_PRODUCT_MAP = {
    "Electronics": [1, 2, 3, 8, 9, 12, 13, 15],
    "Apparel":     [10, 11, 16],
    "Home":        [4, 14, 17],
    "Sports":      [5, 18, 19, 20],
    "Beauty":      [6, 16],
    "Toys":        [7],
}
ALL_PRODUCT_IDS = list(range(1, 21))


def _pick_product_for_session(session_category: str) -> int:
    """
    Returns a product ID biased toward the session's category interest.
    80% of the time stays in-category, 20% explores randomly.
    """
    if random.random() < 0.80 and session_category in CATEGORY_PRODUCT_MAP:
        candidates = CATEGORY_PRODUCT_MAP[session_category]
        return random.choice(candidates)
    return random.choice(ALL_PRODUCT_IDS)


def run_simulation():
    client      = get_redis_sync()
    stream_name = "ingestion_stream"

    # Pre-generate a small pool of sessions, each with a preferred category
    NUM_SESSIONS  = 40
    sessions = {
        f"sess_{1000 + i}": random.choice(list(CATEGORY_PRODUCT_MAP.keys()))
        for i in range(NUM_SESSIONS)
    }

    print("[Producer] Starting session-aware traffic simulation to Redis Streams…")
    time.sleep(3)  # wait for consumer / setup

    while True:
        try:
            num_events = random.randint(1, 15)

            for _ in range(num_events):
                # Pick a session with its category bias
                session_id       = random.choice(list(sessions.keys()))
                session_category = sessions[session_id]
                prod_target      = _pick_product_for_session(session_category)

                event_type = random.choice(["VIEW", "VIEW", "VIEW", "ADD_TO_CART"])

                payload = {
                    "type":       event_type,
                    "productId":  f"prod-{prod_target}",
                    "sessionId":  session_id,
                    "category":   session_category,
                    "ts":         time.strftime("%H:%M:%S"),
                }
                client.xadd(stream_name, {"payload": json.dumps(payload)})

            time.sleep(random.uniform(0.5, 2.0))

        except Exception as e:
            print(f"[Producer] Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run_simulation()
