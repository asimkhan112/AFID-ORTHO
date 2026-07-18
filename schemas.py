"""Pydantic request/response schemas."""
from pydantic import BaseModel, EmailStr, Field, validator, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    """User roles."""
    HOD = "hod"
    DOCTOR = "doctor"
    RECEPTION = "reception"


class StatusEnum(str, Enum):
    """Account status."""
    ACTIVE = "Active"
    ON_LEAVE = "On Leave"
    INACTIVE = "Inactive"


class VisitStatusEnum(str, Enum):
    """Visit status."""
    WAITING = "Waiting"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class LeaveStatusEnum(str, Enum):
    """Leave request status."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


# ──────────────────── Auth Schemas ────────────────────
class LoginRequest(BaseModel):
    """Login request payload."""
    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None  # Will be dict instead of AccountResponse


# ──────────────────── Account Schemas ────────────────────
class AccountBase(BaseModel):
    """Base account information."""
    name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    rank: str = Field(..., min_length=1, max_length=100)
    dept: str = Field(..., min_length=1, max_length=255)
    status: StatusEnum = StatusEnum.ACTIVE
    role: Optional[RoleEnum] = None


class AccountCreate(AccountBase):
    """Create account request."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum() or '_' in v, 'Username must be alphanumeric'
        return v


class AccountUpdate(BaseModel):
    """Update account request."""
    name: Optional[str] = None
    title: Optional[str] = None
    rank: Optional[str] = None
    dept: Optional[str] = None
    status: Optional[StatusEnum] = None
    role: Optional[RoleEnum] = None


class PasswordUpdate(BaseModel):
    """Change an account password."""
    password: str = Field(..., min_length=6)


class AccountResponse(BaseModel):
    """Account response."""
    id: str
    name: str
    title: str
    rank: str
    dept: str
    initials: str
    status: StatusEnum
    role: Optional[RoleEnum]
    username: Optional[str]
    is_seeded: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────── Patient Schemas ────────────────────
class PatientBase(BaseModel):
    """Base patient information."""
    mr_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    rank: str = Field(..., min_length=1, max_length=100)
    doctor_id: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    """Update patient request."""
    name: Optional[str] = None
    rank: Optional[str] = None
    doctor_id: Optional[str] = None


class PatientResponse(PatientBase):
    """Patient response."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ──────────────────── Visit Schemas ────────────────────
class VisitBase(BaseModel):
    """Base visit information."""
    patient_id: str
    doctor_id: Optional[str] = None
    room_id: Optional[str] = None
    visit_time: str = Field(..., description="Time in HH:MM format")
    visit_type: str = Field(..., min_length=1, max_length=50)
    status: VisitStatusEnum = VisitStatusEnum.WAITING
    notes: Optional[str] = None


class VisitCreate(VisitBase):
    pass


class VisitUpdate(BaseModel):
    """Update visit request."""
    doctor_id: Optional[str] = None
    room_id: Optional[str] = None
    status: Optional[VisitStatusEnum] = None
    notes: Optional[str] = None


class VisitResponse(VisitBase):
    """Visit response."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ──────────────────── Room Schemas ────────────────────
class RoomBase(BaseModel):
    """Base room information."""
    number: str = Field(..., min_length=1, max_length=20)
    doctor_id: Optional[str] = None
    capacity: int = Field(default=2, ge=1, le=10)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    """Update room request."""
    doctor_id: Optional[str] = None
    capacity: Optional[int] = None


class RoomResponse(RoomBase):
    """Room response."""
    id: str
    patient_count: int
    status: str  # "Available", "Occupied", "Full"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ──────────────────── Leave Request Schemas ────────────────────
class LeaveRequestBase(BaseModel):
    """Base leave request information."""
    leave_type: str = Field(..., min_length=1, max_length=50)
    from_date: datetime
    to_date: datetime
    reason: str = Field(..., min_length=1)
    
    @validator('to_date')
    def to_date_after_from_date(cls, v, values):
        if 'from_date' in values and v <= values['from_date']:
            raise ValueError('to_date must be after from_date')
        return v


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestDecide(BaseModel):
    """Approve/reject leave request."""
    status: LeaveStatusEnum
    decision_note: Optional[str] = None


class LeaveRequestResponse(LeaveRequestBase):
    """Leave request response."""
    id: str
    requester_id: str
    status: LeaveStatusEnum
    decided_by_id: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_note: Optional[str] = None
    created_at: datetime
    submitted_at: datetime
    
    class Config:
        from_attributes = True


# ──────────────────── Message Schemas ────────────────────
class MessageBase(BaseModel):
    """Base message information."""
    conversation_id: str = Field(..., description="dm:<id>|<id> or channel:department")
    text: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    """Message response."""
    id: str
    sender_id: str
    created_at: datetime
    read_by: List[str] = []

    @field_validator("read_by", mode="before")
    @classmethod
    def _account_ids(cls, value):
        """The ORM relationship yields Account rows; expose their ids as strings."""
        if not value:
            return []
        return [getattr(item, "id", item) for item in value]

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation with messages."""
    conversation_id: str
    messages: List[MessageResponse]


# ──────────────────── Template Schemas ────────────────────
class TemplatePayload(BaseModel):
    """Template payload content."""
    diagnoses: List[dict] = []
    procedures: List[dict] = []
    medications: List[dict] = []
    investigations: List[dict] = []
    materials: List[dict] = []
    notes_cc: str = ""
    notes_hpi: str = ""
    notes_extra_oral: str = ""
    notes_intra_oral: str = ""
    notes_diag: str = ""
    notes_treat: str = ""
    notes_followup: str = ""
    disposition: str = "Follow-up"


class TemplateBase(BaseModel):
    """Base template information."""
    name: str = Field(..., min_length=1, max_length=255)
    template_type: str = Field(..., min_length=1, max_length=50)
    scope: str = Field(..., description="'department' or 'personal'")
    status: str = "Active"
    payload: TemplatePayload


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    """Update template request."""
    name: Optional[str] = None
    status: Optional[str] = None
    payload: Optional[TemplatePayload] = None


class TemplateResponse(TemplateBase):
    """Template response."""
    id: str
    owner_id: Optional[str] = None
    usages: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──────────────────── Patient Journey (Care Pathway) Schemas ────────────────────
class JourneyKindEnum(str, Enum):
    NEW = "New"
    RETURNING = "Returning"
    FOLLOWUP = "Follow-up"


class JourneyStatusEnum(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class JourneyStepCreate(BaseModel):
    """One stop in the pathway."""
    doctor_id: str = Field(..., description="Doctor account id for this step")
    step_purpose: str = Field(..., min_length=1, max_length=255, description="Activity, e.g. 'X-Ray'")
    room_id: Optional[str] = None


class JourneyCreate(BaseModel):
    """Reception creates a pathway of ordered steps for a patient."""
    patient_id: str
    visit_kind: JourneyKindEnum
    steps: List[JourneyStepCreate] = Field(..., min_length=1)


class JourneyStepResponse(BaseModel):
    id: str
    sequence: int
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    room: Optional[str] = None
    step_purpose: Optional[str] = None
    status: str
    is_current: bool = False
    arrived_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JourneyResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    mr_number: str
    visit_kind: JourneyKindEnum
    status: JourneyStatusEnum
    current_step_id: Optional[str] = None
    steps: List[JourneyStepResponse] = []
    created_at: datetime
    completed_at: Optional[datetime] = None


class AddStepRequest(BaseModel):
    """Append a step to an existing journey (e.g. a doctor referring onward)."""
    doctor_id: str
    step_purpose: str = Field(..., min_length=1, max_length=255)
    room_id: Optional[str] = None


class TrackStepInfo(BaseModel):
    doctor_name: Optional[str] = None
    room: Optional[str] = None
    step_purpose: Optional[str] = None
    status: Optional[str] = None


class TrackResponse(BaseModel):
    """What reception sees when tracking a patient for a relative."""
    found: bool
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    mr_number: Optional[str] = None
    journey_id: Optional[str] = None
    journey_status: Optional[str] = None
    # Human phrase, e.g. "Currently doing X-Ray with Dr. Malik in Room 1".
    current_activity: Optional[str] = None
    step_index: Optional[int] = None      # 1-based position of the current step
    total_steps: Optional[int] = None
    current: Optional[TrackStepInfo] = None
    next: Optional[TrackStepInfo] = None
    message: Optional[str] = None         # friendly message when not found / finished
