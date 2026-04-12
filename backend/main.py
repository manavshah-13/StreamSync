import sys, os
# Ensure backend/ is on the path regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middleware.monitor  import LatencyMonitorMiddleware
from api.routes import products, analytics, pricing, ml_admin
from api.routes import search, ml_insights
from engine.latency_tracker import LatencyMiddleware

app = FastAPI(title="StreamSync Backend")

# ── Middleware (outermost runs first) ─────────────────────────────────────────
app.add_middleware(LatencyMiddleware)
app.add_middleware(LatencyMonitorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(products.router,    prefix="/api")
app.include_router(analytics.router,   prefix="/api")
app.include_router(pricing.router,     prefix="/api")
app.include_router(ml_admin.router,    prefix="/api")
app.include_router(search.router,      prefix="/api")
app.include_router(ml_insights.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "StreamSync Backend is alive!"}
