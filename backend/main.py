import sys, os
# Ensure backend/ is on the path regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middleware.monitor  import LatencyMonitorMiddleware
from api.routes import products, analytics, pricing, ml_admin, auth, admin_routes
from api.routes import search, ml_insights, events
from app.api.v1.endpoints import recommendations
from engine.latency_tracker import LatencyMiddleware
from db.database import engine
from models import schema
from core.redis import redis_service

# Create DB tables
schema.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis connection pool
    await redis_service.init_pool()
    # Trigger background startup synchronization of product embeddings cache
    try:
        from app.core.lifecycle import register_startup_sync
        register_startup_sync(app)
    except Exception as e:
        import logging
        logging.getLogger("main").warning(
            f"Failed to register startup sync task: {e}. Gateway starting in fallback mode."
        )
    yield
    # Shutdown: Clean up Redis connection pool
    await redis_service.close_pool()

app = FastAPI(title="StreamSync Backend", lifespan=lifespan)

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
app.include_router(auth.router,        prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(events.router,     prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "StreamSync Backend is alive!"}
