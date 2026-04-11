from fastapi import FastAPI
from api.middleware.monitor import LatencyMonitorMiddleware
from api.routes import products, analytics, pricing, ml_admin
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StreamSync Backend")

# Middleware
app.add_middleware(LatencyMonitorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(products.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(pricing.router, prefix="/api")
app.include_router(ml_admin.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "StreamSync Backend is alive!"}
