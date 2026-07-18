"""API route handlers for visit management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import VisitCreate, VisitResponse, VisitUpdate
from services import VisitService
from dependencies import get_current_user
from models import Account
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/visits", tags=["Visits"])


@router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    visit_data: VisitCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Create a new patient visit. Requires authentication.
    
    - **patient_id**: Patient ID
    - **visit_time**: Time in HH:MM format (e.g., "09:30")
    - **visit_type**: Type of visit (Follow-up, New Consultation, Adjustment, etc.)
    - **doctor_id**: Assigned doctor ID (optional)
    - **room_id**: Assigned room ID (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        visit = VisitService.create_visit(db, visit_data)
        return VisitResponse.model_validate(visit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[VisitResponse])
async def list_visits(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List all visits.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    visits = VisitService.list_visits(db, skip=skip, limit=limit)
    return [VisitResponse.model_validate(v) for v in visits]


@router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get visit by ID."""
    visit = VisitService.get_visit(db, visit_id)
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return VisitResponse.model_validate(visit)


@router.patch("/{visit_id}", response_model=VisitResponse)
async def update_visit(
    visit_id: str,
    update_data: VisitUpdate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Update visit details."""
    visit = VisitService.get_visit(db, visit_id)
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    
    # Update fields if provided
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    
    db.add(visit)
    db.commit()
    db.refresh(visit)
    
    return VisitResponse.model_validate(visit)


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visit(
    visit_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Delete a visit."""
    try:
        VisitService.delete_visit(db, visit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{visit_id}/assign-doctor/{doctor_id}", response_model=VisitResponse)
async def assign_doctor_to_visit(
    visit_id: str,
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Assign a doctor to a visit."""
    try:
        visit = VisitService.assign_doctor(db, visit_id, doctor_id)
        return VisitResponse.model_validate(visit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{visit_id}/assign-room/{room_id}", response_model=VisitResponse)
async def assign_room_to_visit(
    visit_id: str,
    room_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Assign a room to a visit."""
    try:
        visit = VisitService.assign_room(db, visit_id, room_id)
        return VisitResponse.model_validate(visit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
