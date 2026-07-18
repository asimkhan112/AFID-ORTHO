"""API route handlers for data exports (Excel)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
from typing import Optional
import logging

from database import get_db
from dependencies import get_current_doctor
from models import Account, Visit, Patient
from excel_export import build_daily_queue_workbook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/daily-queue")
async def export_daily_queue(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_doctor),
    for_date: Optional[date] = Query(
        default=None, alias="date", description="Queue date (YYYY-MM-DD). Defaults to today."
    ),
):
    """Export the signed-in doctor's patient queue for a date as an .xlsx file.

    Only visits belonging to the authenticated doctor are included. Returns 404
    with a friendly message when the queue is empty (no empty file is produced).
    """
    target = for_date or datetime.now(timezone.utc).date()

    try:
        # Single join query, scoped to this doctor only, ordered by time.
        results = (
            db.query(Visit, Patient)
            .join(Patient, Visit.patient_id == Patient.id)
            .filter(Visit.doctor_id == current_user.id)
            .filter(func.date(Visit.created_at) == target)
            .order_by(Visit.visit_time.asc(), Visit.created_at.asc())
            .all()
        )
    except Exception:
        logger.exception("Failed to load daily queue for doctor %s on %s", current_user.id, target)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read the queue from the database. Please try again.",
        )

    if not results:
        # Friendly, explicit message — the client shows this to the doctor.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No patients in your queue for {target.isoformat()}.",
        )

    rows = []
    for index, (visit, patient) in enumerate(results, start=1):
        visit_date = visit.created_at.date().isoformat() if visit.created_at else target.isoformat()
        rows.append(
            {
                "queue_number": index,
                "patient_id": patient.mr_number,
                "patient_name": patient.name,
                # Age / Gender / per-visit Diagnosis are not stored in the schema.
                "age": None,
                "gender": None,
                "visit_date": visit_date,
                "visit_time": visit.visit_time,
                "diagnosis": None,
                "procedure": visit.visit_type,
                "status": visit.status.value if hasattr(visit.status, "value") else str(visit.status),
                "doctor_name": current_user.name,
            }
        )

    try:
        workbook_bytes = build_daily_queue_workbook(rows, target, current_user.name)
    except Exception:
        logger.exception("Failed to generate workbook for doctor %s on %s", current_user.id, target)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate the Excel file. Please try again.",
        )

    safe_user = (current_user.username or "doctor").replace("/", "_")
    filename = f"daily-queue-{safe_user}-{target.isoformat()}.xlsx"
    logger.info("Exported daily queue: %d rows for doctor %s (%s)", len(rows), current_user.id, target)

    return Response(
        content=workbook_bytes,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
