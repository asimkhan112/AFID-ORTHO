"""API route handlers for account management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import AccountCreate, AccountResponse, AccountUpdate, PasswordUpdate
from services import AccountService
from dependencies import get_current_user, get_current_hod
from models import Account
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_hod)
):
    """
    Create a new account. Only HOD can create accounts.
    
    - **name**: Full name
    - **title**: Job title (e.g., "Orthodontist")
    - **rank**: Military rank
    - **dept**: Department
    - **username**: Unique username for login
    - **password**: Password (minimum 6 characters)
    - **role**: User role (hod, doctor, reception, or null for no portal access)
    - **status**: Account status (Active, On Leave, Inactive)
    """
    try:
        account = AccountService.create_account(db, account_data)
        return AccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
    role: str = Query(None, description="Filter by role"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List all accounts with optional role filter.
    
    - **role**: Filter by role (hod, doctor, reception)
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    accounts = AccountService.list_accounts(db, role=role, skip=skip, limit=limit)
    return [AccountResponse.model_validate(acc) for acc in accounts]


@router.get("/me", response_model=AccountResponse)
async def get_current_profile(
    current_user: Account = Depends(get_current_user)
):
    """Get current user profile."""
    return AccountResponse.model_validate(current_user)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get account by ID."""
    account = AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    update_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_hod)
):
    """Update an account. Only HOD can update accounts."""
    try:
        account = AccountService.update_account(
            db, account_id, update_data.model_dump(exclude_unset=True)
        )
        return AccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{account_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    account_id: str,
    body: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Change a password. HOD may change anyone's; others only their own."""
    from models import RoleEnum
    if current_user.role != RoleEnum.HOD and current_user.id != account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change another user's password")
    try:
        AccountService.set_password(db, account_id, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_hod)
):
    """Delete a non-seeded account. Only HOD can delete accounts."""
    try:
        AccountService.delete_account(db, account_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
