"""API route handlers for room management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import RoomCreate, RoomResponse, RoomUpdate
from services import RoomService
from dependencies import get_current_user
from models import Account
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Create a new treatment room.
    
    - **number**: Room number/identifier (unique)
    - **capacity**: Room capacity (default: 2, min: 1, max: 10)
    - **doctor_id**: Assigned doctor ID (optional)
    """
    try:
        room = RoomService.create_room(db, room_data)
        return RoomResponse.model_validate(room)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List all treatment rooms.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    rooms = RoomService.list_rooms(db, skip=skip, limit=limit)
    return [RoomResponse.model_validate(r) for r in rooms]


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get room by ID."""
    room = RoomService.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return RoomResponse.model_validate(room)


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    update_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Update room details."""
    room = RoomService.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    
    db.add(room)
    db.commit()
    db.refresh(room)
    
    return RoomResponse.model_validate(room)


@router.post("/{room_id}/assign-doctor/{doctor_id}", response_model=RoomResponse)
async def assign_doctor_to_room(
    room_id: str,
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Assign a doctor to a room."""
    try:
        room = RoomService.assign_doctor_to_room(db, room_id, doctor_id)
        return RoomResponse.model_validate(room)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
