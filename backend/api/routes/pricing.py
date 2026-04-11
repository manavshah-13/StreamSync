from fastapi import APIRouter, Depends, Request
from db.redis_client import get_redis
import json

router = APIRouter(prefix="/signals", tags=["Signals"])

@router.post("")
async def receive_signal(request: Request, redis=Depends(get_redis)):
    payload = await request.json()
    
    # Fire and forget into redis ingestion_stream
    await redis.xadd("ingestion_stream", {"payload": json.dumps(payload)})
    
    return {"status": "accepted"}
