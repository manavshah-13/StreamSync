from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import Optional, Union
from pydantic import BaseModel

from db.database import get_db
from models.schema import Experiment, ExperimentResult

router = APIRouter(prefix="/experiments", tags=["Experiments"])

class TrackEventRequest(BaseModel):
    experiment_id: Union[int, str]
    variant_group: str
    event_type: str
    revenue: Optional[float] = 0.0

@router.post("/track")
async def track_experiment_event(
    payload: TrackEventRequest,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/experiments/track
    Tracks experiment conversions and revenue updates atomically.
    """
    # 1. Resolve experiment_id
    actual_exp_id = None
    # If the experiment_id looks like an integer (either int or all digits string)
    if isinstance(payload.experiment_id, int) or (isinstance(payload.experiment_id, str) and payload.experiment_id.isdigit()):
        actual_exp_id = int(payload.experiment_id)
        # Verify it exists by ID
        exp = db.query(Experiment).filter(Experiment.id == actual_exp_id).first()
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID {actual_exp_id} not found."
            )
    else:
        # Otherwise treat it as the experiment name/key
        exp = db.query(Experiment).filter(Experiment.name == payload.experiment_id).first()
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with name '{payload.experiment_id}' not found."
            )
        actual_exp_id = exp.id

    # Normalize variant group to upper case (e.g. 'A' or 'B')
    variant_group = payload.variant_group.upper()

    try:
        # Check if the result row for this experiment and variant group exists.
        result_exists = db.query(ExperimentResult).filter(
            ExperimentResult.experiment_id == actual_exp_id,
            ExperimentResult.variant_group == variant_group
        ).first()

        # Is this event a conversion? Increment conversions accordingly
        is_conversion = payload.event_type.lower() == "conversion" or payload.event_type.lower() == "purchase"
        increment_conv = 1 if is_conversion else 0

        if not result_exists:
            # Create the initial row
            new_result = ExperimentResult(
                experiment_id=actual_exp_id,
                variant_group=variant_group,
                conversions=increment_conv,
                total_revenue=payload.revenue or 0.0
            )
            db.add(new_result)
            db.commit()
        else:
            # Perform atomic database update to prevent race conditions
            stmt = (
                update(ExperimentResult)
                .where(
                    ExperimentResult.experiment_id == actual_exp_id,
                    ExperimentResult.variant_group == variant_group
                )
                .values(
                    conversions=ExperimentResult.conversions + increment_conv,
                    total_revenue=ExperimentResult.total_revenue + (payload.revenue or 0.0)
                )
            )
            db.execute(stmt)
            db.commit()
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track experiment event: {e}"
        )

    return {"status": "success", "message": "Event tracked successfully."}
