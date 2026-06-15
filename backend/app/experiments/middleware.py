from fastapi import Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from models.schema import Experiment
from app.experiments.router_logic import assign_experiment_variant

async def get_experiment_variant(
    x_session_id: Optional[str] = Header(None, alias="x-session-id"),
    x_user_id: Optional[str] = Header(None, alias="x-user-id"),
    db: Session = Depends(get_db)
) -> str:
    """
    FastAPI dependency that evaluates active experiments in the database
    and statelessly assigns the incoming request to variant group 'A' or 'B'.
    
    If no user/session identifier is provided, or no active experiment exists
    in the database, it defaults gracefully to variant 'A' (control).
    """
    # Prefer user_id, fall back to session_id
    identifier = x_user_id or x_session_id
    
    # If no identifier headers are provided, default to 'A'
    if not identifier:
        return "A"
        
    try:
        # Check if there is an active experiment in the database
        active_exp = db.query(Experiment).filter(Experiment.is_active == True).first()
        if not active_exp:
            return "A"
            
        # Compute variant group using MD5 hashing router logic
        return assign_experiment_variant(identifier, active_exp.name)
    except Exception as e:
        # Default gracefully to variant 'A' in case of any database or processing error
        return "A"
