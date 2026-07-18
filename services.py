"""Business logic services."""
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
from models import Account, Patient, Visit, Room, LeaveRequest, Message, Template
from schemas import (
    AccountCreate, PatientCreate, VisitCreate, RoomCreate, 
    LeaveRequestCreate, LeaveRequestDecide, MessageCreate
)
from auth import hash_password, verify_password, create_access_token
from models import RoleEnum, StatusEnum, VisitStatusEnum, LeaveStatusEnum
import logging
import json

logger = logging.getLogger(__name__)


# ──────────────────── Account Service ────────────────────
class AccountService:
    """Account/User management."""
    
    @staticmethod
    def create_account(db: Session, account: AccountCreate) -> Account:
        """Create a new account."""
        # Check if username already exists
        existing = db.query(Account).filter(Account.username == account.username).first()
        if existing:
            raise ValueError(f"Username '{account.username}' already exists")
        
        # Create initials from name
        initials = "".join([word[0].upper() for word in account.name.split()[:2]])
        
        db_account = Account(
            name=account.name,
            title=account.title,
            rank=account.rank,
            dept=account.dept,
            initials=initials,
            status=account.status,
            username=account.username,
            password_hash=hash_password(account.password),
            role=account.role,
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        return db_account
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[Account]:
        """Get account by username."""
        return db.query(Account).filter(Account.username == username).first()
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[Account]:
        """Authenticate user with username and password."""
        account = AccountService.get_by_username(db, username)
        if not account or not account.password_hash:
            return None
        
        if not verify_password(password, account.password_hash):
            return None
        
        return account
    
    @staticmethod
    def get_account(db: Session, account_id: str) -> Optional[Account]:
        """Get account by ID."""
        return db.query(Account).filter(Account.id == account_id).first()
    
    @staticmethod
    def list_accounts(db: Session, role: Optional[str] = None, skip: int = 0, limit: int = 100):
        """List all accounts with optional role filter."""
        query = db.query(Account)
        if role:
            query = query.filter(Account.role == role)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_account(db: Session, account_id: str, updates: dict) -> Account:
        """Update mutable fields on an account."""
        account = AccountService.get_account(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        allowed = {"name", "title", "rank", "dept", "status", "role"}
        for field, value in updates.items():
            if field in allowed and value is not None:
                setattr(account, field, value)

        # Keep initials in sync when the name changes.
        if updates.get("name"):
            account.initials = "".join(word[0].upper() for word in account.name.split()[:2])

        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def set_password(db: Session, account_id: str, new_password: str) -> Account:
        """Update an account password."""
        account = AccountService.get_account(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        account.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def delete_account(db: Session, account_id: str) -> None:
        """Delete a non-seeded account."""
        account = AccountService.get_account(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        if account.is_seeded:
            raise ValueError("Seeded accounts cannot be deleted")
        db.delete(account)
        db.commit()


# ──────────────────── Patient Service ────────────────────
class PatientService:
    """Patient management."""
    
    @staticmethod
    def create_patient(db: Session, patient: PatientCreate) -> Patient:
        """Create a new patient."""
        existing = db.query(Patient).filter(Patient.mr_number == patient.mr_number).first()
        if existing:
            raise ValueError(f"Patient with MR Number '{patient.mr_number}' already exists")
        
        db_patient = Patient(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    
    @staticmethod
    def get_patient(db: Session, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        return db.query(Patient).filter(Patient.id == patient_id).first()
    
    @staticmethod
    def list_patients(db: Session, skip: int = 0, limit: int = 100):
        """List all patients."""
        return db.query(Patient).offset(skip).limit(limit).all()

    @staticmethod
    def update_patient(db: Session, patient_id: str, updates: dict) -> Patient:
        """Update mutable patient fields."""
        patient = PatientService.get_patient(db, patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        for field, value in updates.items():
            if value is not None:
                setattr(patient, field, value)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def delete_patient(db: Session, patient_id: str) -> None:
        """Delete a patient (cascades to their visits)."""
        patient = PatientService.get_patient(db, patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        db.delete(patient)
        db.commit()


# ──────────────────── Visit Service ────────────────────
class VisitService:
    """Visit management."""
    
    @staticmethod
    def create_visit(db: Session, visit: VisitCreate) -> Visit:
        """Create a new visit."""
        db_visit = Visit(**visit.model_dump())
        db.add(db_visit)
        db.commit()
        db.refresh(db_visit)
        return db_visit
    
    @staticmethod
    def get_visit(db: Session, visit_id: str) -> Optional[Visit]:
        """Get visit by ID."""
        return db.query(Visit).filter(Visit.id == visit_id).first()
    
    @staticmethod
    def list_visits(db: Session, skip: int = 0, limit: int = 100):
        """List all visits."""
        return db.query(Visit).offset(skip).limit(limit).all()
    
    @staticmethod
    def assign_doctor(db: Session, visit_id: str, doctor_id: str) -> Visit:
        """Assign a doctor to a visit."""
        visit = VisitService.get_visit(db, visit_id)
        if not visit:
            raise ValueError(f"Visit {visit_id} not found")
        
        visit.doctor_id = doctor_id
        visit.status = VisitStatusEnum.ASSIGNED
        db.commit()
        db.refresh(visit)
        return visit
    
    @staticmethod
    def assign_room(db: Session, visit_id: str, room_id: str) -> Visit:
        """Assign a room to a visit."""
        visit = VisitService.get_visit(db, visit_id)
        if not visit:
            raise ValueError(f"Visit {visit_id} not found")
        
        visit.room_id = room_id
        db.commit()
        db.refresh(visit)
        return visit
    
    @staticmethod
    def update_visit_status(db: Session, visit_id: str, status: VisitStatusEnum) -> Visit:
        """Update visit status."""
        visit = VisitService.get_visit(db, visit_id)
        if not visit:
            raise ValueError(f"Visit {visit_id} not found")
        
        visit.status = status
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def delete_visit(db: Session, visit_id: str) -> None:
        """Delete a visit."""
        visit = VisitService.get_visit(db, visit_id)
        if not visit:
            raise ValueError(f"Visit {visit_id} not found")
        db.delete(visit)
        db.commit()


# ──────────────────── Room Service ────────────────────
class RoomService:
    """Room management."""
    
    @staticmethod
    def create_room(db: Session, room: RoomCreate) -> Room:
        """Create a new room."""
        existing = db.query(Room).filter(Room.number == room.number).first()
        if existing:
            raise ValueError(f"Room '{room.number}' already exists")
        
        db_room = Room(**room.model_dump())
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        return db_room
    
    @staticmethod
    def get_room(db: Session, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        return db.query(Room).filter(Room.id == room_id).first()
    
    @staticmethod
    def list_rooms(db: Session, skip: int = 0, limit: int = 100):
        """List all rooms."""
        return db.query(Room).offset(skip).limit(limit).all()
    
    @staticmethod
    def assign_doctor_to_room(db: Session, room_id: str, doctor_id: str) -> Room:
        """Assign a doctor to a room."""
        room = RoomService.get_room(db, room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")
        
        room.doctor_id = doctor_id
        db.commit()
        db.refresh(room)
        return room


# ──────────────────── Leave Request Service ────────────────────
class LeaveService:
    """Leave request management."""
    
    @staticmethod
    def create_leave_request(db: Session, requester_id: str, leave: LeaveRequestCreate) -> LeaveRequest:
        """Create a new leave request."""
        db_leave = LeaveRequest(
            requester_id=requester_id,
            leave_type=leave.leave_type,
            from_date=leave.from_date,
            to_date=leave.to_date,
            reason=leave.reason,
        )
        db.add(db_leave)
        db.commit()
        db.refresh(db_leave)
        return db_leave
    
    @staticmethod
    def get_leave_request(db: Session, leave_id: str) -> Optional[LeaveRequest]:
        """Get leave request by ID."""
        return db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    @staticmethod
    def list_leave_requests(db: Session, skip: int = 0, limit: int = 100):
        """List all leave requests."""
        return db.query(LeaveRequest).offset(skip).limit(limit).all()
    
    @staticmethod
    def list_user_leave(db: Session, requester_id: str):
        """List leave requests for a specific user."""
        return db.query(LeaveRequest).filter(LeaveRequest.requester_id == requester_id).all()
    
    @staticmethod
    def decide_leave_request(db: Session, leave_id: str, decided_by_id: str, decision: LeaveRequestDecide) -> LeaveRequest:
        """Approve or reject a leave request."""
        leave = LeaveService.get_leave_request(db, leave_id)
        if not leave:
            raise ValueError(f"Leave request {leave_id} not found")
        
        if leave.status != LeaveStatusEnum.PENDING:
            raise ValueError(f"Can only decide pending requests, current status: {leave.status}")
        
        leave.status = decision.status
        leave.decided_by_id = decided_by_id
        leave.decided_at = datetime.now(timezone.utc)
        leave.decision_note = decision.decision_note

        db.commit()
        db.refresh(leave)
        return leave

    @staticmethod
    def cancel_leave_request(db: Session, leave_id: str, requester_id: str) -> None:
        """Cancel (delete) a pending leave request. Only the requester may cancel."""
        leave = LeaveService.get_leave_request(db, leave_id)
        if not leave:
            raise ValueError(f"Leave request {leave_id} not found")
        if leave.requester_id != requester_id:
            raise PermissionError("You can only cancel your own leave requests")
        if leave.status != LeaveStatusEnum.PENDING:
            raise ValueError("Only pending requests can be cancelled")
        db.delete(leave)
        db.commit()


# ──────────────────── Message Service ────────────────────
class MessageService:
    """Message management."""
    
    @staticmethod
    def send_message(db: Session, sender_id: str, message: MessageCreate) -> Message:
        """Send a message."""
        db_message = Message(
            conversation_id=message.conversation_id,
            sender_id=sender_id,
            text=message.text,
        )
        db_message.read_by.append(db.query(Account).filter(Account.id == sender_id).first())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    
    @staticmethod
    def get_message(db: Session, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        return db.query(Message).filter(Message.id == message_id).first()
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: str):
        """Get all messages in a conversation."""
        return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
    
    @staticmethod
    def mark_as_read(db: Session, message_id: str, account_id: str) -> Message:
        """Mark a message as read by an account."""
        message = MessageService.get_message(db, message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if account and account not in message.read_by:
            message.read_by.append(account)
            db.commit()
            db.refresh(message)
        
        return message


# ──────────────────── Template Service ────────────────────
class TemplateService:
    """Template management."""
    
    @staticmethod
    def create_template(db: Session, owner_id: Optional[str], template_data: dict) -> Template:
        """Create a new template."""
        db_template = Template(
            name=template_data['name'],
            template_type=template_data['template_type'],
            scope=template_data['scope'],
            owner_id=owner_id,
            status=template_data.get('status', 'Active'),
            diagnoses=json.dumps(template_data.get('payload', {}).get('diagnoses', [])),
            procedures=json.dumps(template_data.get('payload', {}).get('procedures', [])),
            medications=json.dumps(template_data.get('payload', {}).get('medications', [])),
            investigations=json.dumps(template_data.get('payload', {}).get('investigations', [])),
            materials=json.dumps(template_data.get('payload', {}).get('materials', [])),
            notes_cc=template_data.get('payload', {}).get('notes_cc', ''),
            notes_hpi=template_data.get('payload', {}).get('notes_hpi', ''),
            notes_extra_oral=template_data.get('payload', {}).get('notes_extra_oral', ''),
            notes_intra_oral=template_data.get('payload', {}).get('notes_intra_oral', ''),
            notes_diag=template_data.get('payload', {}).get('notes_diag', ''),
            notes_treat=template_data.get('payload', {}).get('notes_treat', ''),
            notes_followup=template_data.get('payload', {}).get('notes_followup', ''),
            disposition=template_data.get('payload', {}).get('disposition', 'Follow-up'),
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    
    @staticmethod
    def get_template(db: Session, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        return db.query(Template).filter(Template.id == template_id).first()
    
    @staticmethod
    def list_templates(db: Session, scope: Optional[str] = None, owner_id: Optional[str] = None,
                       include_department: bool = False, skip: int = 0, limit: int = 100):
        """List templates.

        - HOD (owner_id=None): every template.
        - Others (owner_id set, include_department=True): department templates
          (owner_id IS NULL) plus their own personal templates.
        """
        query = db.query(Template)
        if scope:
            query = query.filter(Template.scope == scope)
        if owner_id is not None:
            if include_department:
                query = query.filter((Template.owner_id == owner_id) | (Template.owner_id.is_(None)))
            else:
                query = query.filter(Template.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def use_template(db: Session, template_id: str) -> Template:
        """Increment usage counter."""
        template = TemplateService.get_template(db, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        template.usages += 1
        template.last_used = datetime.now(timezone.utc)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: str) -> None:
        """Delete a template."""
        template = TemplateService.get_template(db, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        db.delete(template)
        db.commit()
