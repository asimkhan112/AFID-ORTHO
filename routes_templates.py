"""API route handlers for templates."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import TemplateCreate, TemplateResponse, TemplateUpdate
from services import TemplateService
from dependencies import get_current_user, get_current_doctor, get_current_hod
from models import Account, RoleEnum
import logging


def _is_hod(user: Account) -> bool:
    """True when the account holds the HOD role."""
    return user.role == RoleEnum.HOD

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Create a new template.
    
    For department templates, only HOD can create (scope='department', owner_id=null).
    For personal templates, doctors can create (scope='personal', owner_id=user).
    
    - **name**: Template name
    - **template_type**: Type (Diagnosis, Procedure, Clinical Notes, Medication, Materials)
    - **scope**: 'department' or 'personal'
    - **payload**: Template content (diagnoses, procedures, medications, investigations, materials, notes)
    """
    # Validate scope and permissions
    if template_data.scope == "department" and not _is_hod(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HOD can create department templates"
        )
    
    owner_id = None if template_data.scope == "department" else current_user.id
    
    try:
        template = TemplateService.create_template(db, owner_id, template_data.model_dump())
        return TemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),
    scope: str = Query(None, description="'department' or 'personal'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List templates.
    
    - **scope**: Filter by scope (department or personal)
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    
    Non-HOD users see: all department templates + their personal templates
    HOD users see: all department and personal templates
    """
    is_hod = _is_hod(current_user)
    owner_filter = None if is_hod else current_user.id

    templates = TemplateService.list_templates(
        db,
        scope=scope,
        owner_id=owner_filter,
        include_department=not is_hod,
        skip=skip,
        limit=limit
    )

    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Get template by ID."""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return TemplateResponse.model_validate(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    update_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Update template (only owner or HOD can update)."""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    # Check permissions
    if template.owner_id and template.owner_id != current_user.id and not _is_hod(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this template"
        )
    
    # Update fields if provided
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if field == "payload" and value:
            # Reconstruct the flat storage columns from the nested payload.
            payload_dict = value.model_dump() if hasattr(value, 'model_dump') else value
            template.apply_payload(payload_dict)
        else:
            setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)
    
    return TemplateResponse.model_validate(template)


@router.post("/{template_id}/use", response_model=TemplateResponse)
async def use_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Increment template usage counter."""
    try:
        template = TemplateService.use_template(db, template_id)
        return TemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Delete a template (only owner or HOD)."""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    if template.owner_id and template.owner_id != current_user.id and not _is_hod(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete this template")
    TemplateService.delete_template(db, template_id)
