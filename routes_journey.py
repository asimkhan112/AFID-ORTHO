"""API route handlers for patient journeys (care pathways)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from database import get_db
from dependencies import get_current_user, get_current_doctor
from models import Account
from schemas import JourneyCreate, JourneyResponse, AddStepRequest, TrackResponse
import journey_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/journeys", tags=["Patient Journey"])


@router.post("", response_model=JourneyResponse, status_code=status.HTTP_201_CREATED)
async def create_journey(
    body: JourneyCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
):
    """Reception builds a care path (ordered steps) for a patient."""
    try:
        journey = journey_service.create_journey(
            db,
            created_by_id=current_user.id,
            patient_id=body.patient_id,
            visit_kind=body.visit_kind.value,
            steps=[s.model_dump() for s in body.steps],
        )
        return journey_service.serialize_journey(db, journey)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# NOTE: static paths declared before "/{journey_id}" so they are not shadowed.
@router.get("/track", response_model=TrackResponse)
async def track_patient(
    q: str = Query(..., description="Patient name or MR number"),
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
):
    """Find a patient and report what they are doing right now (for relatives)."""
    return journey_service.track_patient(db, q)


@router.get("/steps/mine")
async def my_steps(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_doctor),
):
    """The signed-in doctor's current, actionable journey steps."""
    return journey_service.steps_for_doctor(db, current_user.id)


@router.get("/{journey_id}", response_model=JourneyResponse)
async def get_journey(
    journey_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
):
    journey = journey_service.get_journey(db, journey_id)
    if not journey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return journey_service.serialize_journey(db, journey)


@router.post("/steps/{step_id}/start", response_model=JourneyResponse)
async def start_step(
    step_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
):
    """Doctor marks their current step as In Progress."""
    try:
        journey = journey_service.start_step(db, step_id, current_user.id)
        return journey_service.serialize_journey(db, journey)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/steps/{step_id}/complete", response_model=JourneyResponse)
async def complete_step(
    step_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
):
    """Doctor completes their step; the patient advances to the next one."""
    try:
        journey = journey_service.complete_step(db, step_id, current_user.id)
        return journey_service.serialize_journey(db, journey)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{journey_id}/steps", response_model=JourneyResponse)
async def add_step(
    journey_id: str,
    body: AddStepRequest,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
):
    """Append a step to a journey (doctor referring the patient onward)."""
    try:
        journey = journey_service.add_step(db, journey_id, body.doctor_id, body.step_purpose, body.room_id)
        return journey_service.serialize_journey(db, journey)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
