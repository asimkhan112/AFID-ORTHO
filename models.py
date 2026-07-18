"""SQLAlchemy ORM models."""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Enum, Table, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from enum import Enum as PyEnum
import uuid


def _enum_values(enum_cls):
    """Return the human-readable enum *values* (e.g. "Active", "hod") for the
    column definition, so the DB stores values rather than member NAMES.

    This keeps stored data aligned with the API/schema strings and lets the
    service layer accept either the ORM enum or the Pydantic schema enum
    (both share the same value) without a LookupError.
    """
    return [member.value for member in enum_cls]


# Convenience: an Enum column that persists by value.
def ValueEnum(enum_cls, **kwargs):
    return Enum(enum_cls, values_callable=_enum_values, **kwargs)


class RoleEnum(PyEnum):
    """User role enumeration."""
    HOD = "hod"
    DOCTOR = "doctor"
    RECEPTION = "reception"


class StatusEnum(PyEnum):
    """Account status enumeration."""
    ACTIVE = "Active"
    ON_LEAVE = "On Leave"
    INACTIVE = "Inactive"


class VisitStatusEnum(PyEnum):
    """Visit status enumeration."""
    WAITING = "Waiting"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class LeaveStatusEnum(PyEnum):
    """Leave request status enumeration."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class JourneyKindEnum(PyEnum):
    """How the patient is arriving for this journey."""
    NEW = "New"
    RETURNING = "Returning"
    FOLLOWUP = "Follow-up"


class JourneyStatusEnum(PyEnum):
    """Overall status of a patient journey (care pathway)."""
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


# Association tables
message_read_by = Table(
    'message_read_by',
    Base.metadata,
    Column('message_id', String(36), ForeignKey('message.id', ondelete='CASCADE')),
    Column('account_id', String(36), ForeignKey('account.id', ondelete='CASCADE')),
)


class Account(Base):
    """Staff directory and authentication model."""
    __tablename__ = "account"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)  # Job title
    rank = Column(String(100), nullable=False)
    dept = Column(String(255), nullable=False)
    initials = Column(String(10), nullable=False)
    status = Column(ValueEnum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)

    # Auth fields
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(ValueEnum(RoleEnum), nullable=True)  # null = support staff, no portal access
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_seeded = Column(Boolean, default=False)  # Can't delete seeded records
    
    # Relationships
    visits = relationship("Visit", back_populates="doctor", foreign_keys="Visit.doctor_id")
    rooms = relationship("Room", back_populates="doctor")
    leave_requests = relationship("LeaveRequest", back_populates="requester", foreign_keys="LeaveRequest.requester_id")
    leave_decisions = relationship("LeaveRequest", back_populates="decided_by_user", foreign_keys="LeaveRequest.decided_by_id")
    sent_messages = relationship("Message", back_populates="sender")
    
    def __repr__(self):
        return f"<Account {self.username}>"


class Patient(Base):
    """Patient records."""
    __tablename__ = "patient"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mr_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    rank = Column(String(100), nullable=False)
    doctor_id = Column(String(36), ForeignKey("account.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient {self.mr_number}: {self.name}>"


class Visit(Base):
    """Patient visit scheduling and tracking."""
    __tablename__ = "visit"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("account.id"), nullable=True)
    room_id = Column(String(36), ForeignKey("room.id"), nullable=True)
    
    visit_time = Column(String(5), nullable=False)  # "09:30" format
    visit_type = Column(String(50), nullable=False)  # "Follow-up", "New Consultation", etc.
    status = Column(ValueEnum(VisitStatusEnum), default=VisitStatusEnum.WAITING, nullable=False)
    notes = Column(Text, nullable=True)

    # ── Care-pathway (journey) fields ────────────────────────────────────────
    # A visit doubles as a *step* in a patient journey. These are null for
    # standalone visits, so nothing about the existing visit flow changes.
    journey_id = Column(String(36), ForeignKey("patient_journey.id", ondelete="CASCADE"), nullable=True, index=True)
    sequence = Column(Integer, nullable=True)            # step order within the journey (1, 2, 3…)
    step_purpose = Column(String(255), nullable=True)    # human activity label, e.g. "X-Ray", "Consultation"
    arrived_at = Column(DateTime, nullable=True)         # became the current step (entered this doctor's queue)
    started_at = Column(DateTime, nullable=True)         # doctor began the step
    completed_at = Column(DateTime, nullable=True)       # step finished

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="visits")
    doctor = relationship("Account", back_populates="visits", foreign_keys=[doctor_id])
    room = relationship("Room", back_populates="visits")
    journey = relationship("PatientJourney", back_populates="steps", foreign_keys=[journey_id])

    def __repr__(self):
        return f"<Visit {self.id}: {self.patient_id} @ {self.visit_time}>"


class Room(Base):
    """Treatment room management."""
    __tablename__ = "room"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(String(20), unique=True, nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("account.id"), nullable=True)
    capacity = Column(Integer, default=2, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctor = relationship("Account", back_populates="rooms")
    visits = relationship("Visit", back_populates="room")
    
    @property
    def patient_count(self):
        """Count active patients in this room."""
        return sum(1 for visit in self.visits if visit.status in [VisitStatusEnum.IN_PROGRESS])
    
    @property
    def status(self):
        """Compute room status: Available, Occupied, or Full."""
        if self.patient_count >= self.capacity:
            return "Full"
        elif self.patient_count > 0:
            return "Occupied"
        return "Available"
    
    def __repr__(self):
        return f"<Room {self.number}>"


class LeaveRequest(Base):
    """Leave request workflow."""
    __tablename__ = "leave_request"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id = Column(String(36), ForeignKey("account.id"), nullable=False)
    
    leave_type = Column(String(50), nullable=False)  # "Annual Leave", "Sick Leave", etc.
    from_date = Column(DateTime, nullable=False)
    to_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    
    status = Column(ValueEnum(LeaveStatusEnum), default=LeaveStatusEnum.PENDING, nullable=False)
    
    # Decision tracking
    decided_by_id = Column(String(36), ForeignKey("account.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requester = relationship("Account", back_populates="leave_requests", foreign_keys=[requester_id])
    decided_by_user = relationship("Account", back_populates="leave_decisions", foreign_keys=[decided_by_id])
    
    def __repr__(self):
        return f"<LeaveRequest {self.id}: {self.leave_type}>"


class Message(Base):
    """Direct messages and department channel."""
    __tablename__ = "message"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(100), nullable=False, index=True)  # "dm:<a>|<b>" or "channel:department"
    sender_id = Column(String(36), ForeignKey("account.id"), nullable=False)
    
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Read tracking
    read_by = relationship("Account", secondary=message_read_by, backref="read_messages")
    
    # Relationships
    sender = relationship("Account", back_populates="sent_messages")
    
    def __repr__(self):
        return f"<Message {self.id}: {self.conversation_id}>"


class Template(Base):
    """Worksheet templates."""
    __tablename__ = "template"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    template_type = Column(String(50), nullable=False)  # "Diagnosis", "Procedure", "Clinical Notes", "Medication", "Materials"
    scope = Column(String(20), nullable=False)  # "department" or "personal"
    owner_id = Column(String(36), ForeignKey("account.id"), nullable=True)  # null for department templates
    
    status = Column(String(20), default="Active", nullable=False)  # "Active" or "Draft"
    
    # Payload (stored as JSON text)
    diagnoses = Column(Text, default="[]")
    procedures = Column(Text, default="[]")
    medications = Column(Text, default="[]")
    investigations = Column(Text, default="[]")
    materials = Column(Text, default="[]")
    notes_cc = Column(Text, default="")
    notes_hpi = Column(Text, default="")
    notes_extra_oral = Column(Text, default="")
    notes_intra_oral = Column(Text, default="")
    notes_diag = Column(Text, default="")
    notes_treat = Column(Text, default="")
    notes_followup = Column(Text, default="")
    disposition = Column(String(100), default="Follow-up")
    
    usages = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def _load_json(raw):
        """Parse a JSON-text column into a list, tolerating null/blank/corrupt."""
        import json
        if not raw:
            return []
        try:
            value = json.loads(raw)
            return value if isinstance(value, list) else []
        except (ValueError, TypeError):
            return []

    @property
    def payload(self):
        """Reconstruct the nested payload object the API exposes from the flat
        columns used for storage. Consumed by TemplateResponse (from_attributes)."""
        return {
            "diagnoses": self._load_json(self.diagnoses),
            "procedures": self._load_json(self.procedures),
            "medications": self._load_json(self.medications),
            "investigations": self._load_json(self.investigations),
            "materials": self._load_json(self.materials),
            "notes_cc": self.notes_cc or "",
            "notes_hpi": self.notes_hpi or "",
            "notes_extra_oral": self.notes_extra_oral or "",
            "notes_intra_oral": self.notes_intra_oral or "",
            "notes_diag": self.notes_diag or "",
            "notes_treat": self.notes_treat or "",
            "notes_followup": self.notes_followup or "",
            "disposition": self.disposition or "Follow-up",
        }

    def apply_payload(self, payload: dict):
        """Persist a payload dict back into the flat columns (JSON for lists)."""
        import json
        list_fields = ("diagnoses", "procedures", "medications", "investigations", "materials")
        for field in list_fields:
            if field in payload:
                setattr(self, field, json.dumps(payload[field] or []))
        note_fields = (
            "notes_cc", "notes_hpi", "notes_extra_oral", "notes_intra_oral",
            "notes_diag", "notes_treat", "notes_followup", "disposition",
        )
        for field in note_fields:
            if field in payload and payload[field] is not None:
                setattr(self, field, payload[field])

    def __repr__(self):
        return f"<Template {self.name}>"


class PatientJourney(Base):
    """A patient's care pathway — an ordered set of steps (Visit rows).

    Reception builds the pathway; the patient moves through the steps one at a
    time. `current_step_id` records which step (visit) the patient is at right
    now, which powers the "where is my patient / currently doing X" tracking.
    """
    __tablename__ = "patient_journey"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(String(36), ForeignKey("account.id"), nullable=True)  # reception who set it up

    visit_kind = Column(ValueEnum(JourneyKindEnum), nullable=False)
    status = Column(ValueEnum(JourneyStatusEnum), default=JourneyStatusEnum.ACTIVE, nullable=False)

    # Visit id of the step the patient is currently at (plain id, not a FK, to
    # avoid a circular constraint with visit.journey_id). Null when finished.
    current_step_id = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("Patient")
    steps = relationship(
        "Visit",
        back_populates="journey",
        foreign_keys="Visit.journey_id",
        order_by="Visit.sequence",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<PatientJourney {self.id}: {self.status}>"
