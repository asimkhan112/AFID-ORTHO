"""Dependency injection and middleware."""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from auth import decode_token
from models import Account, RoleEnum
import logging

logger = logging.getLogger(__name__)


async def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
) -> Account:
    """Get the current authenticated user."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(Account).filter(Account.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_hod(current_user: Account = Depends(get_current_user)) -> Account:
    """Require HOD role."""
    if current_user.role != RoleEnum.HOD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HOD can access this resource"
        )
    return current_user


async def get_current_doctor(current_user: Account = Depends(get_current_user)) -> Account:
    """Require Doctor role."""
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this resource"
        )
    return current_user


async def get_current_reception(current_user: Account = Depends(get_current_user)) -> Account:
    """Require Reception role."""
    if current_user.role != RoleEnum.RECEPTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reception staff can access this resource"
        )
    return current_user
