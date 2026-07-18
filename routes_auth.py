"""API route handlers for authentication."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from schemas import LoginRequest, TokenResponse, AccountResponse
from services import AccountService
from auth import create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    - **username**: Account username
    - **password**: Account password
    
    Returns JWT token valid for 30 minutes.
    """
    # Authenticate user
    user = AccountService.authenticate(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "title": user.title,
            "rank": user.rank,
            "dept": user.dept,
            "initials": user.initials,
            "status": user.status.value,
            "role": user.role.value if user.role else None,
            "username": user.username,
            "created_at": user.created_at.isoformat()
        }
    }
