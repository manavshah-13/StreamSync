import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from db.redis_client import get_redis_sync

class LatencyMonitorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
         super().__init__(app)
         self.redis = get_redis_sync()
         
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Fire-and-forget metric recording to calculate p99
        try:
            self.redis.lpush("latency_log", process_time)
            self.redis.ltrim("latency_log", 0, 999) # Keep 1K requests
        except Exception:
            pass
            
        return response
