"""API route handlers for patient management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import PatientCreate, PatientResponse, PatientUpdate
from services import PatientService
from dependencies import get_current_user
from models import Account
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Create a new patient record. Requires authentication.
    
    - **mr_number**: Medical record number (unique)
    - **name**: Patient name
    - **rank**: Military rank
    - **doctor_id**: Assigned doctor ID (optional)
    """
    try:
        patient = PatientService.create_patient(db, patient_data)
        return PatientResponse.model_validate(patient)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List all patients.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    patients = PatientService.list_patients(db, skip=skip, limit=limit)
    return [PatientResponse.model_validate(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get patient by ID."""
    patient = PatientService.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    update_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Update a patient record."""
    try:
        patient = PatientService.update_patient(
            db, patient_id, update_data.model_dump(exclude_unset=True)
        )
        return PatientResponse.model_validate(patient)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Delete a patient (and their visits)."""
    try:
        PatientService.delete_patient(db, patient_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
