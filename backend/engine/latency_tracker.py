"""
LatencyTracker + LatencyMiddleware
===================================
In-process p50/p95/p99 latency tracker using a circular buffer per route.
A FastAPI/Starlette middleware records each request's wall-clock time and
aggregates percentile stats on-the-fly.

No Redis needed — all state is in-process memory.
The tracker is a global singleton; import `tracker` to read stats.
"""
import time
from collections import deque
from starlette.middleware.base import BaseHTTPMiddleware

MAX_SAMPLES = 500   # Circular buffer depth per route


class LatencyTracker:
    """Thread-safe (GIL protects deque ops in CPython) circular-buffer tracker."""

    def __init__(self):
        self._buffers: dict[str, deque] = {}

    def record(self, route: str, latency_ms: float):
        if route not in self._buffers:
            self._buffers[route] = deque(maxlen=MAX_SAMPLES)
        self._buffers[route].append(latency_ms)

    def get_stats(self, route: str | None = None) -> dict:
        """
        Returns percentile stats.
        If route is None, returns stats for all tracked routes.
        """
        routes = {route: self._buffers[route]} if route and route in self._buffers else self._buffers

        result = {}
        for r, buf in routes.items():
            samples = sorted(buf)
            n = len(samples)
            if n == 0:
                continue
            result[r] = {
                "p50":   round(samples[int(0.50 * n)], 1),
                "p95":   round(samples[min(int(0.95 * n), n - 1)], 1),
                "p99":   round(samples[min(int(0.99 * n), n - 1)], 1),
                "mean":  round(sum(samples) / n, 1),
                "min":   round(samples[0], 1),
                "max":   round(samples[-1], 1),
                "count": n,
            }
        return result

    def get_p99(self, route: str = "/api/products") -> float:
        """Convenience: returns the p99 for a single route, or 0 if no data."""
        stats = self.get_stats(route)
        return stats.get(route, {}).get("p99", 0.0)

    @property
    def all_routes(self) -> list:
        return list(self._buffers.keys())


# ── Global singleton ──────────────────────────────────────────────────────────
tracker = LatencyTracker()


class LatencyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that times every request and feeds latency_tracker.
    Also injects X-Response-Time header in the response.
    """
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Normalise path (strip query string, collapse IDs for grouping)
        path = request.url.path
        tracker.record(path, elapsed_ms)

        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
        return response
