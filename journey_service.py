"""Patient journey (care pathway) business logic.

A journey is an ordered list of steps; each step is a Visit row. Exactly one
step is "current" at a time (`journey.current_step_id`), which drives the live
"where is my patient / currently doing X" tracking.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging

from sqlalchemy.orm import Session

from models import (
    PatientJourney, Visit, Patient, Account, Room,
    JourneyKindEnum, JourneyStatusEnum, VisitStatusEnum,
)

logger = logging.getLogger(__name__)


# ──────────────────────────── helpers ────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _doctor_name(db: Session, doctor_id: Optional[str]) -> Optional[str]:
    if not doctor_id:
        return None
    acc = db.query(Account).filter(Account.id == doctor_id).first()
    return acc.name if acc else None


def _room_number(db: Session, step: Visit) -> Optional[str]:
    """Room for a step: its explicit room, else the doctor's assigned room."""
    if step.room_id:
        room = db.query(Room).filter(Room.id == step.room_id).first()
        if room:
            return room.number
    if step.doctor_id:
        room = db.query(Room).filter(Room.doctor_id == step.doctor_id).first()
        if room:
            return room.number
    return None


def _status_value(status) -> str:
    return status.value if hasattr(status, "value") else str(status)


def serialize_step(db: Session, step: Visit, current_step_id: Optional[str]) -> Dict:
    return {
        "id": step.id,
        "sequence": step.sequence or 0,
        "doctor_id": step.doctor_id,
        "doctor_name": _doctor_name(db, step.doctor_id),
        "room": _room_number(db, step),
        "step_purpose": step.step_purpose,
        "status": _status_value(step.status),
        "is_current": step.id == current_step_id,
        "arrived_at": step.arrived_at,
        "started_at": step.started_at,
        "completed_at": step.completed_at,
    }


def serialize_journey(db: Session, journey: PatientJourney) -> Dict:
    patient = journey.patient or db.query(Patient).filter(Patient.id == journey.patient_id).first()
    steps = sorted(journey.steps, key=lambda s: s.sequence or 0)
    return {
        "id": journey.id,
        "patient_id": journey.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "mr_number": patient.mr_number if patient else "",
        "visit_kind": _status_value(journey.visit_kind),
        "status": _status_value(journey.status),
        "current_step_id": journey.current_step_id,
        "steps": [serialize_step(db, s, journey.current_step_id) for s in steps],
        "created_at": journey.created_at,
        "completed_at": journey.completed_at,
    }


# ──────────────────────────── operations ─────────────────────────────────────

def get_active_journey_for_patient(db: Session, patient_id: str) -> Optional[PatientJourney]:
    return (
        db.query(PatientJourney)
        .filter(PatientJourney.patient_id == patient_id, PatientJourney.status == JourneyStatusEnum.ACTIVE)
        .first()
    )


def create_journey(db: Session, created_by_id: str, patient_id: str, visit_kind: str, steps: List[Dict]) -> PatientJourney:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise ValueError("Patient not found")
    if get_active_journey_for_patient(db, patient_id):
        raise ValueError("This patient already has an active care path.")
    if not steps:
        raise ValueError("A care path needs at least one step.")

    journey = PatientJourney(
        patient_id=patient_id,
        created_by_id=created_by_id,
        visit_kind=JourneyKindEnum(visit_kind),
        status=JourneyStatusEnum.ACTIVE,
    )
    db.add(journey)
    db.flush()  # assign journey.id

    now = _now()
    time_label = now.strftime("%H:%M")
    first_step_id = None
    for index, step in enumerate(steps, start=1):
        is_first = index == 1
        room_id = step.get("room_id")
        if not room_id and step.get("doctor_id"):
            room = db.query(Room).filter(Room.doctor_id == step["doctor_id"]).first()
            room_id = room.id if room else None
        visit = Visit(
            patient_id=patient_id,
            doctor_id=step.get("doctor_id"),
            room_id=room_id,
            visit_time=time_label,
            visit_type=(step.get("step_purpose") or "Step")[:50],
            step_purpose=step.get("step_purpose"),
            journey_id=journey.id,
            sequence=index,
            status=VisitStatusEnum.WAITING if is_first else VisitStatusEnum.ASSIGNED,
            arrived_at=now if is_first else None,
        )
        db.add(visit)
        db.flush()
        if is_first:
            first_step_id = visit.id

    journey.current_step_id = first_step_id
    db.commit()
    db.refresh(journey)
    logger.info("Created journey %s for patient %s with %d steps", journey.id, patient_id, len(steps))
    return journey


def get_journey(db: Session, journey_id: str) -> Optional[PatientJourney]:
    return db.query(PatientJourney).filter(PatientJourney.id == journey_id).first()


def _require_step(db: Session, step_id: str) -> Visit:
    step = db.query(Visit).filter(Visit.id == step_id, Visit.journey_id.isnot(None)).first()
    if not step:
        raise ValueError("Journey step not found")
    return step


def start_step(db: Session, step_id: str, doctor_id: str) -> PatientJourney:
    step = _require_step(db, step_id)
    if step.doctor_id != doctor_id:
        raise PermissionError("You can only start your own step.")
    step.status = VisitStatusEnum.IN_PROGRESS
    step.started_at = _now()
    db.commit()
    return get_journey(db, step.journey_id)


def complete_step(db: Session, step_id: str, doctor_id: str) -> PatientJourney:
    """Complete the doctor's step and advance the patient to the next one."""
    step = _require_step(db, step_id)
    if step.doctor_id != doctor_id:
        raise PermissionError("You can only complete your own step.")

    now = _now()
    step.status = VisitStatusEnum.COMPLETED
    step.completed_at = now

    journey = get_journey(db, step.journey_id)
    next_step = (
        db.query(Visit)
        .filter(Visit.journey_id == journey.id, Visit.sequence > (step.sequence or 0))
        .order_by(Visit.sequence.asc())
        .first()
    )
    if next_step:
        next_step.status = VisitStatusEnum.WAITING
        next_step.arrived_at = now
        journey.current_step_id = next_step.id
    else:
        journey.status = JourneyStatusEnum.COMPLETED
        journey.completed_at = now
        journey.current_step_id = None

    db.commit()
    db.refresh(journey)
    logger.info("Completed step %s; journey %s now %s", step_id, journey.id, _status_value(journey.status))
    return journey


def add_step(db: Session, journey_id: str, doctor_id: str, step_purpose: str, room_id: Optional[str] = None) -> PatientJourney:
    """Append a step (e.g. a doctor referring the patient onward)."""
    journey = get_journey(db, journey_id)
    if not journey:
        raise ValueError("Journey not found")

    max_seq = max((s.sequence or 0 for s in journey.steps), default=0)
    if not room_id and doctor_id:
        room = db.query(Room).filter(Room.doctor_id == doctor_id).first()
        room_id = room.id if room else None

    now = _now()
    # If nothing is currently active, this new step becomes the current one.
    activate = journey.current_step_id is None
    visit = Visit(
        patient_id=journey.patient_id,
        doctor_id=doctor_id,
        room_id=room_id,
        visit_time=now.strftime("%H:%M"),
        visit_type=(step_purpose or "Step")[:50],
        step_purpose=step_purpose,
        journey_id=journey.id,
        sequence=max_seq + 1,
        status=VisitStatusEnum.WAITING if activate else VisitStatusEnum.ASSIGNED,
        arrived_at=now if activate else None,
    )
    db.add(visit)
    db.flush()
    if activate:
        journey.current_step_id = visit.id
        journey.status = JourneyStatusEnum.ACTIVE
        journey.completed_at = None
    db.commit()
    db.refresh(journey)
    return journey


def steps_for_doctor(db: Session, doctor_id: str) -> List[Dict]:
    """Current, actionable steps for a doctor (patients with them right now)."""
    rows = (
        db.query(Visit, PatientJourney, Patient)
        .join(PatientJourney, PatientJourney.id == Visit.journey_id)
        .join(Patient, Patient.id == Visit.patient_id)
        .filter(
            PatientJourney.status == JourneyStatusEnum.ACTIVE,
            PatientJourney.current_step_id == Visit.id,
            Visit.doctor_id == doctor_id,
        )
        .order_by(Visit.arrived_at.asc())
        .all()
    )
    out = []
    for visit, journey, patient in rows:
        step = serialize_step(db, visit, journey.current_step_id)
        step["journey_id"] = journey.id
        step["patient_id"] = patient.id
        step["patient_name"] = patient.name
        step["mr_number"] = patient.mr_number
        step["visit_kind"] = _status_value(journey.visit_kind)
        out.append(step)
    return out


def track_patient(db: Session, query: str) -> Dict:
    """Locate a patient and describe what they are doing right now."""
    q = (query or "").strip()
    if not q:
        return {"found": False, "message": "Enter a patient name or MR number to search."}

    like = f"%{q}%"
    patient = (
        db.query(Patient)
        .filter((Patient.mr_number.ilike(like)) | (Patient.name.ilike(like)))
        .order_by(Patient.name.asc())
        .first()
    )
    if not patient:
        return {"found": False, "message": f"No patient found matching '{q}'."}

    journey = get_active_journey_for_patient(db, patient.id)
    base = {
        "found": True,
        "patient_id": patient.id,
        "patient_name": patient.name,
        "mr_number": patient.mr_number,
    }
    if not journey:
        return {**base, "message": f"{patient.name} has no active visit right now."}

    steps = sorted(journey.steps, key=lambda s: s.sequence or 0)
    current = next((s for s in steps if s.id == journey.current_step_id), None)
    total = len(steps)

    if not current:
        return {**base, "journey_id": journey.id, "journey_status": _status_value(journey.status),
                "total_steps": total, "message": f"{patient.name}'s visit is complete."}

    doctor_name = _doctor_name(db, current.doctor_id) or "the assigned doctor"
    room = _room_number(db, current)
    purpose = current.step_purpose or current.visit_type or "their appointment"
    status = _status_value(current.status)
    where = f" in {room}" if room else ""

    if status == "In Progress":
        activity = f"Currently doing {purpose} with {doctor_name}{where}."
    elif status == "Waiting":
        activity = f"Waiting for {purpose} — {doctor_name}{where}."
    else:
        activity = f"{purpose} — {doctor_name}{where} ({status})."

    next_step = next((s for s in steps if (s.sequence or 0) > (current.sequence or 0)), None)
    next_info = None
    if next_step:
        next_info = {
            "doctor_name": _doctor_name(db, next_step.doctor_id),
            "room": _room_number(db, next_step),
            "step_purpose": next_step.step_purpose,
            "status": _status_value(next_step.status),
        }

    return {
        **base,
        "journey_id": journey.id,
        "journey_status": _status_value(journey.status),
        "current_activity": activity,
        "step_index": current.sequence,
        "total_steps": total,
        "current": {"doctor_name": doctor_name, "room": room, "step_purpose": purpose, "status": status},
        "next": next_info,
    }
