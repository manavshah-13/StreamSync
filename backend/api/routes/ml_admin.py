import os
import json
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from db.redis_client import get_redis

# The API Key defaults to the env variable, or our safe fallback
API_KEY = os.getenv("ML_API_KEY", "ml-dev-secret-key-12345")
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

router = APIRouter(prefix="/ml-admin", tags=["ML Developer"])

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Unauthorized ML API Key"
    )

@router.get("/raw-stream")
async def get_raw_ingestion_stream(limit: int = 100, redis=Depends(get_redis), api_key: str = Depends(get_api_key)):
    """
    Requires X-API-Key Header.
    Allows the ML Developer to pull raw untethered session data for training models.
    """
    raw_data = await redis.xrange("ingestion_stream", "-", "+", limit)
    
    parsed = []
    if raw_data:
        for msg_id, payload in raw_data:
            data_dict = {}
            for k, v in payload.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                try:
                    data_dict[key_str] = json.loads(val_str)
                except:
                    data_dict[key_str] = val_str
            
            parsed.append({
                "message_id": msg_id.decode('utf-8') if isinstance(msg_id, bytes) else msg_id,
                "data": data_dict
            })
            
    return {"status": "success", "count": len(parsed), "events": parsed}
