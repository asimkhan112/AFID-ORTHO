"""API route handlers for leave requests."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import LeaveRequestCreate, LeaveRequestResponse, LeaveRequestDecide
from services import LeaveService
from dependencies import get_current_user, get_current_hod
from models import Account
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leave", tags=["Leave Requests"])


@router.post("", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_leave_request(
    leave_data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Submit a new leave request.
    
    - **leave_type**: Type of leave (Annual Leave, Sick Leave, Training Leave, etc.)
    - **from_date**: Start date (ISO format)
    - **to_date**: End date (ISO format, must be after from_date)
    - **reason**: Reason for leave request
    """
    try:
        leave_request = LeaveService.create_leave_request(db, current_user.id, leave_data)
        return LeaveRequestResponse.model_validate(leave_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[LeaveRequestResponse])
async def list_leave_requests(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List all leave requests (HOD sees all, others see their own).
    
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    if current_user.role and current_user.role.value == "hod":
        requests = LeaveService.list_leave_requests(db, skip=skip, limit=limit)
    else:
        requests = LeaveService.list_user_leave(db, current_user.id)
    
    return [LeaveRequestResponse.model_validate(lr) for lr in requests]


@router.get("/my-requests", response_model=list[LeaveRequestResponse])
async def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get current user's leave requests."""
    requests = LeaveService.list_user_leave(db, current_user.id)
    return [LeaveRequestResponse.model_validate(lr) for lr in requests]


@router.get("/{leave_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    leave_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get leave request by ID."""
    leave_request = LeaveService.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    return LeaveRequestResponse.model_validate(leave_request)


@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_leave_request(
    leave_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Cancel your own pending leave request."""
    try:
        LeaveService.cancel_leave_request(db, leave_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{leave_id}/decide", response_model=LeaveRequestResponse)
async def decide_leave_request(
    leave_id: str,
    decision: LeaveRequestDecide,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_hod)
):
    """
    Approve or reject a leave request. Only HOD can decide.
    
    - **status**: Approved or Rejected
    - **decision_note**: Optional note for the decision
    """
    try:
        leave_request = LeaveService.decide_leave_request(db, leave_id, current_user.id, decision)
        return LeaveRequestResponse.model_validate(leave_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
