import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from db.database import get_db
from models.schema import User, OnboardingPreferences
from api.auth_utils import SECRET_KEY, ALGORITHM
from pydantic import BaseModel

router = APIRouter(tags=["Users"])

class OnboardingPayload(BaseModel):
    age_group: str
    gender: str
    interests: List[str]
    shopping_preferences: Dict[str, Any]

@router.post("/users/onboarding", status_code=status.HTTP_201_CREATED)
def save_onboarding(
    payload: OnboardingPayload,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user_id = None
    
    # 1. Try to get user from Authorization token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = decoded.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    user_id = user.id
        except JWTError:
            pass

    # 2. If no authenticated user, create a unique guest user
    if not user_id:
        guest_uuid = str(uuid.uuid4())
        guest_email = f"guest-{guest_uuid}@streamsync.com"
        from api.auth_utils import get_password_hash
        hashed_pw = get_password_hash(guest_uuid)
        
        guest_user = User(
            email=guest_email,
            full_name=f"Guest {guest_uuid[:8]}",
            hashed_password=hashed_pw,
            is_admin=False
        )
        db.add(guest_user)
        db.commit()
        db.refresh(guest_user)
        user_id = guest_user.id

    # 3. Create or update OnboardingPreferences for this user
    pref = db.query(OnboardingPreferences).filter(OnboardingPreferences.user_id == user_id).first()
    if not pref:
        pref = OnboardingPreferences(
            user_id=user_id,
            gender=payload.gender,
            age_group=payload.age_group,
            interests=payload.interests,
            shopping_preferences=payload.shopping_preferences
        )
        db.add(pref)
    else:
        pref.gender = payload.gender
        pref.age_group = payload.age_group
        pref.interests = payload.interests
        pref.shopping_preferences = payload.shopping_preferences

    db.commit()
    db.refresh(pref)

    # 4. Generate a session ID
    session_id = f"session-{uuid.uuid4()}"

    return {
        "status": "success",
        "user_id": user_id,
        "session_id": session_id
    }
