import json
from enum import Enum
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import redis.asyncio as aioredis
from core.redis import get_redis

# Create the FastAPI router
router = APIRouter(tags=["Events"])

# Define allowed event type choices
class EventType(str, Enum):
    click = "click"
    view = "view"
    cart_add = "cart_add"
    cart_remove = "cart_remove"
    wishlist = "wishlist"
    checkout = "checkout"
    purchase = "purchase"

# Define validation schema for incoming tracking payloads
class UserEventSchema(BaseModel):
    user_id: str = Field(..., description="String or UUID identifying the user")
    session_id: str = Field(..., description="String identifying the user's session")
    event_type: EventType = Field(..., description="Restricted category of user interaction")
    sku: str = Field(..., description="Stock keeping unit of the product")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional nested metadata payload")

@router.post("/events", status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event: UserEventSchema,
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Ingest a user interaction event.
    Appends the event data directly into a Redis Stream for async consumption in O(1) time.
    """
    try:
        # Extract fields to write to the Redis Stream (flat dict of string key-values)
        fields = {
            "user_id": event.user_id,
            "session_id": event.session_id,
            "event_type": event.event_type.value,
            "sku": event.sku,
            "metadata": json.dumps(event.metadata or {})
        }

        # Appends the fields to the 'stream:user_events' stream using XADD
        redis_stream_id = await redis.xadd(
            name="stream:user_events",
            fields=fields,
            id="*"
        )

        return {
            "status": "queued",
            "event_id": str(redis_stream_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue event: {str(e)}"
        )
