"""Database seeding with comprehensive dummy data."""
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Account, Patient, Visit, Room, LeaveRequest, Message, Template, RoleEnum, StatusEnum, VisitStatusEnum, LeaveStatusEnum
from auth import hash_password
from datetime import datetime, timedelta, timezone
import json
import logging

logger = logging.getLogger(__name__)


def seed_database():
    """Seed the database with comprehensive dummy data."""
    db = SessionLocal()
    
    try:
        # Initialize database tables
        init_db()
        logger.info("✅ Database tables created")
        
        # Check if data already exists
        if db.query(Account).count() > 0:
            logger.info("⚠️  Database already seeded, skipping seed operation")
            return
        
        # ──────────────────── Seed Accounts ────────────────────
        logger.info("Seeding accounts...")
        
        accounts = [
            # HOD
            Account(
                id="u-hod-1",
                name="Col. Al-Mansouri",
                title="Head of Department",
                rank="Colonel",
                dept="Orthodontics",
                initials="AM",
                status=StatusEnum.ACTIVE,
                username="hod.colonel",
                password_hash=hash_password("hod123"),
                role=RoleEnum.HOD,
                is_seeded=True,
            ),
            # Doctors
            Account(
                id="u-doc-1",
                name="Dr. Amna Malik",
                title="Orthodontist · AFID",
                rank="Major",
                dept="Orthodontics",
                initials="AM",
                status=StatusEnum.ACTIVE,
                username="dr.malik",
                password_hash=hash_password("doctor123"),
                role=RoleEnum.DOCTOR,
                is_seeded=True,
            ),
            Account(
                id="u-doc-2",
                name="Dr. Omar Khalil",
                title="Orthodontist",
                rank="Major",
                dept="Orthodontics",
                initials="OK",
                status=StatusEnum.ACTIVE,
                username="dr.khalil",
                password_hash=hash_password("doctor123"),
                role=RoleEnum.DOCTOR,
                is_seeded=True,
            ),
            Account(
                id="u-doc-3",
                name="Dr. Tariq Hassan",
                title="Orthodontist",
                rank="Captain",
                dept="Orthodontics",
                initials="TH",
                status=StatusEnum.ACTIVE,
                username="dr.hassan",
                password_hash=hash_password("doctor123"),
                role=RoleEnum.DOCTOR,
                is_seeded=True,
            ),
            Account(
                id="u-doc-4",
                name="Dr. Layla Al-Amri",
                title="Orthodontist",
                rank="Major",
                dept="Orthodontics",
                initials="LA",
                status=StatusEnum.ON_LEAVE,
                username="dr.amri",
                password_hash=hash_password("doctor123"),
                role=RoleEnum.DOCTOR,
                is_seeded=True,
            ),
            # Reception Staff
            Account(
                id="u-rec-1",
                name="Sgt. Officer",
                title="Reception",
                rank="Sergeant",
                dept="Front Desk",
                initials="SO",
                status=StatusEnum.ACTIVE,
                username="reception.officer",
                password_hash=hash_password("reception123"),
                role=RoleEnum.RECEPTION,
                is_seeded=True,
            ),
            Account(
                id="u-rec-2",
                name="PVT Noura Al-Harbi",
                title="Receptionist",
                rank="Private",
                dept="Front Desk",
                initials="NH",
                status=StatusEnum.ACTIVE,
                username="reception.noura",
                password_hash=hash_password("reception123"),
                role=RoleEnum.RECEPTION,
                is_seeded=True,
            ),
            # Support Staff (no portal access)
            Account(
                id="u-support-1",
                name="SGT Mariam Al-Azmi",
                title="Senior Nurse",
                rank="Sergeant",
                dept="Orthodontics",
                initials="MA",
                status=StatusEnum.ACTIVE,
                username=None,
                password_hash=None,
                role=None,
                is_seeded=True,
            ),
            Account(
                id="u-support-2",
                name="CPL Fahad Al-Subhi",
                title="Dental Technician",
                rank="Corporal",
                dept="Lab",
                initials="FS",
                status=StatusEnum.ACTIVE,
                username=None,
                password_hash=None,
                role=None,
                is_seeded=True,
            ),
        ]
        
        for account in accounts:
            db.add(account)
        db.commit()
        logger.info(f"✅ Seeded {len(accounts)} accounts")
        
        # ──────────────────── Seed Patients (12 patients) ────────────────────
        logger.info("Seeding patients...")
        
        patient_data = [
            ("MAJ Sana Mirza", "Major", "MR-001", "u-doc-1"),
            ("CPT Fatima Ahmad", "Captain", "MR-002", "u-doc-1"),
            ("LT Aisha Khan", "Lieutenant", "MR-003", "u-doc-1"),
            ("SGT Hassan Ali", "Sergeant", "MR-004", "u-doc-2"),
            ("CPL Reem Abdullah", "Corporal", "MR-005", "u-doc-2"),
            ("WO2 Mohammed Al-Qahtani", "Warrant Officer II", "MR-006", "u-doc-2"),
            ("MAJ Zainab Al-Rashid", "Major", "MR-007", "u-doc-3"),
            ("CPT Yusuf Al-Otaibi", "Captain", "MR-008", "u-doc-3"),
            ("LT Lina Al-Dosari", "Lieutenant", "MR-009", "u-doc-3"),
            ("SGT Ahmed Al-Ghamdi", "Sergeant", "MR-010", "u-doc-1"),
            ("CPL Sarah Al-Malki", "Corporal", "MR-011", "u-doc-2"),
            ("PVT Khaled Al-Harbi", "Private", "MR-012", "u-doc-3"),
        ]
        
        patients = []
        for i, (name, rank, mr_number, doctor_id) in enumerate(patient_data):
            patient = Patient(
                id=f"p-{i+1}",
                mr_number=mr_number,
                name=name,
                rank=rank,
                doctor_id=doctor_id,
            )
            patients.append(patient)
            db.add(patient)
        
        db.commit()
        logger.info(f"✅ Seeded {len(patients)} patients")
        
        # ──────────────────── Seed Rooms ────────────────────
        logger.info("Seeding rooms...")
        
        rooms = [
            Room(id="r-1", number="Room 1", doctor_id="u-doc-1", capacity=2),
            Room(id="r-2", number="Room 2", doctor_id="u-doc-2", capacity=2),
            Room(id="r-3", number="Room 3", doctor_id="u-doc-3", capacity=2),
            Room(id="r-4", number="Room 4", doctor_id=None, capacity=1),
            Room(id="r-5", number="Room 5", doctor_id=None, capacity=2),
            Room(id="r-6", number="Emergency Room", doctor_id=None, capacity=1),
        ]
        
        for room in rooms:
            db.add(room)
        db.commit()
        logger.info(f"✅ Seeded {len(rooms)} rooms")
        
        # ──────────────────── Seed Visits ────────────────────
        logger.info("Seeding visits...")
        
        visit_types = ["Follow-up", "New Consultation", "Adjustment", "Emergency", "Records", "Debonding", "Retainer Check"]
        today = datetime.now(timezone.utc)
        
        visits = []
        visit_id = 1
        
        # Create multiple visits for each patient with varied statuses
        for patient in patients:
            for j in range(2):  # 2 visits per patient
                hour = 9 + (j * 2)
                visit_time = f"{hour:02d}:00"
                
                # Assign doctors and rooms
                if visit_id % 2 == 0:
                    doctor_id = "u-doc-1"
                    room_id = "r-1" if visit_id % 3 == 0 else "r-2"
                elif visit_id % 3 == 0:
                    doctor_id = "u-doc-2"
                    room_id = "r-2"
                else:
                    doctor_id = "u-doc-3"
                    room_id = "r-3"
                
                # Vary status
                if visit_id % 5 == 0:
                    status = VisitStatusEnum.COMPLETED
                elif visit_id % 7 == 0:
                    status = VisitStatusEnum.IN_PROGRESS
                elif visit_id % 4 == 0:
                    status = VisitStatusEnum.ASSIGNED
                else:
                    status = VisitStatusEnum.WAITING
                    doctor_id = None
                    room_id = None
                
                visit = Visit(
                    id=f"v-{visit_id}",
                    patient_id=patient.id,
                    doctor_id=doctor_id,
                    room_id=room_id,
                    visit_time=visit_time,
                    visit_type=visit_types[visit_id % len(visit_types)],
                    status=status,
                    notes=f"Visit {visit_id} - {visit_types[visit_id % len(visit_types)]}",
                )
                visits.append(visit)
                db.add(visit)
                visit_id += 1
        
        db.commit()
        logger.info(f"✅ Seeded {len(visits)} visits")
        
        # ──────────────────── Seed Leave Requests ────────────────────
        logger.info("Seeding leave requests...")
        
        leave_types = ["Annual Leave", "Sick Leave", "Training Leave", "Emergency Leave", "Compassionate Leave"]
        
        leave_requests = [
            LeaveRequest(
                id="lv-1",
                requester_id="u-doc-1",
                leave_type=leave_types[0],
                from_date=today + timedelta(days=5),
                to_date=today + timedelta(days=12),
                reason="Annual leave for family vacation",
                status=LeaveStatusEnum.PENDING,
            ),
            LeaveRequest(
                id="lv-2",
                requester_id="u-doc-2",
                leave_type=leave_types[1],
                from_date=today + timedelta(days=1),
                to_date=today + timedelta(days=3),
                reason="Medical appointment",
                status=LeaveStatusEnum.APPROVED,
                decided_by_id="u-hod-1",
                decided_at=today - timedelta(hours=5),
                decision_note="Approved - covered by Dr. Hassan",
            ),
            LeaveRequest(
                id="lv-3",
                requester_id="u-rec-1",
                leave_type=leave_types[2],
                from_date=today + timedelta(days=10),
                to_date=today + timedelta(days=15),
                reason="Professional development course",
                status=LeaveStatusEnum.PENDING,
            ),
            LeaveRequest(
                id="lv-4",
                requester_id="u-doc-3",
                leave_type=leave_types[3],
                from_date=today + timedelta(hours=2),
                to_date=today + timedelta(days=2),
                reason="Family emergency",
                status=LeaveStatusEnum.APPROVED,
                decided_by_id="u-hod-1",
                decided_at=today - timedelta(hours=1),
                decision_note="Approved - emergency leave",
            ),
            LeaveRequest(
                id="lv-5",
                requester_id="u-rec-2",
                leave_type=leave_types[0],
                from_date=today + timedelta(days=20),
                to_date=today + timedelta(days=27),
                reason="Annual entitlement",
                status=LeaveStatusEnum.REJECTED,
                decided_by_id="u-hod-1",
                decided_at=today - timedelta(days=1),
                decision_note="Rejected - insufficient staff coverage",
            ),
        ]
        
        for leave_req in leave_requests:
            db.add(leave_req)
        db.commit()
        logger.info(f"✅ Seeded {len(leave_requests)} leave requests")
        
        # ──────────────────── Seed Messages ────────────────────
        logger.info("Seeding messages...")
        
        messages = [
            # Department channel messages
            Message(
                id="msg-1",
                conversation_id="channel:department",
                sender_id="u-hod-1",
                text="Good morning everyone. Please ensure all patient records are updated by EOD.",
                created_at=today - timedelta(hours=2),
            ),
            Message(
                id="msg-2",
                conversation_id="channel:department",
                sender_id="u-doc-1",
                text="Noted. All records will be updated. Any urgent cases today?",
                created_at=today - timedelta(hours=1.5),
            ),
            Message(
                id="msg-3",
                conversation_id="channel:department",
                sender_id="u-rec-1",
                text="We have 3 emergency walk-ins scheduled for 2 PM.",
                created_at=today - timedelta(hours=1),
            ),
            # Direct message: HOD to Dr. Malik
            Message(
                id="msg-4",
                conversation_id="dm:u-doc-1|u-hod-1",
                sender_id="u-hod-1",
                text="Dr. Malik, please review the treatment plan for patient MR-001",
                created_at=today - timedelta(hours=3),
            ),
            Message(
                id="msg-5",
                conversation_id="dm:u-doc-1|u-hod-1",
                sender_id="u-doc-1",
                text="Already reviewed. Will update in the system by noon.",
                created_at=today - timedelta(hours=2.5),
            ),
            # Direct message: Reception to Dr. Khalil
            Message(
                id="msg-6",
                conversation_id="dm:u-doc-2|u-rec-1",
                sender_id="u-rec-1",
                text="Dr. Khalil, patient CPT Fatima Ahmad has checked in.",
                created_at=today - timedelta(hours=1.5),
            ),
            Message(
                id="msg-7",
                conversation_id="dm:u-doc-2|u-rec-1",
                sender_id="u-doc-2",
                text="Thank you. Please send her to Room 2 in 5 minutes.",
                created_at=today - timedelta(hours=1.25),
            ),
            # Direct message: Dr. Hassan to HOD
            Message(
                id="msg-8",
                conversation_id="dm:u-doc-3|u-hod-1",
                sender_id="u-doc-3",
                text="I have completed initial assessment for 5 new patients. Ready for review.",
                created_at=today - timedelta(minutes=30),
            ),
            Message(
                id="msg-9",
                conversation_id="dm:u-doc-3|u-hod-1",
                sender_id="u-hod-1",
                text="Excellent. Please prepare summary reports for team meeting at 4 PM.",
                created_at=today - timedelta(minutes=20),
            ),
        ]
        
        for msg in messages:
            # Auto-mark sender as read
            msg.read_by.append(db.query(Account).filter(Account.id == msg.sender_id).first())
            db.add(msg)
        
        db.commit()
        logger.info(f"✅ Seeded {len(messages)} messages")

        # ──────────────────── Seed Department Templates ────────────────────
        logger.info("Seeding templates...")

        def tmpl(id, name, ttype, usages, *, diagnoses=None, procedures=None,
                 medications=None, investigations=None, materials=None,
                 cc="", hpi="", extra_oral="", intra_oral="", diag="", treat="",
                 followup="", disposition="Follow-up"):
            return Template(
                id=id, name=name, template_type=ttype, scope="department",
                owner_id=None, status="Active", usages=usages,
                diagnoses=json.dumps(diagnoses or []),
                procedures=json.dumps(procedures or []),
                medications=json.dumps(medications or []),
                investigations=json.dumps(investigations or []),
                materials=json.dumps(materials or []),
                notes_cc=cc, notes_hpi=hpi, notes_extra_oral=extra_oral,
                notes_intra_oral=intra_oral, notes_diag=diag, notes_treat=treat,
                notes_followup=followup, disposition=disposition,
            )

        malocclusion = [{"id": "d1", "code": "K07.3", "label": "Malocclusion Type II, Division 1", "primary": True}]
        templates = [
            tmpl("tpl-1", "Initial Examination", "Diagnosis", 124,
                 diagnoses=malocclusion,
                 investigations=[
                     {"id": "i1", "label": "Panoramic (OPG)", "category": "Radiology", "urgency": "Routine", "reason": "Baseline records"},
                     {"id": "i2", "label": "Lateral Cephalogram", "category": "Radiology", "urgency": "Routine", "reason": "Skeletal assessment"},
                 ],
                 cc="Initial orthodontic consultation",
                 hpi="Patient presents for initial orthodontic assessment. No prior orthodontic treatment.",
                 diag="Class II Division 1 malocclusion with increased overjet.",
                 followup="Return in 2 weeks for treatment plan discussion."),
            tmpl("tpl-2", "Fixed Braces Protocol", "Procedure", 98,
                 diagnoses=malocclusion,
                 procedures=[{"id": "p1", "code": "D8080", "label": "Comprehensive Orthodontic Treatment — Adolescent", "teeth": [], "status": "Planned", "duration": "45 min"}],
                 medications=[{"id": "md1", "drug": "Ibuprofen 400mg", "dose": "400mg", "freq": "TDS", "duration": "5 days", "instructions": "After food"}],
                 cc="Fixed appliance bonding",
                 treat="Upper and lower fixed appliances bonded. Initial archwire placed.",
                 followup="Soft diet 24h. Analgesia as required. Review in 4 weeks."),
            tmpl("tpl-3", "Aligner Progress Note", "Clinical Notes", 73,
                 diagnoses=malocclusion,
                 cc="Aligner progress review",
                 hpi="Patient reports good compliance, wearing aligners 20–22 hours daily.",
                 treat="Next set of aligners issued. IPR performed as per plan.",
                 followup="Change aligners every 7 days. Review in 6 weeks."),
            tmpl("tpl-4", "Post-Treatment Medication", "Medication", 56,
                 medications=[
                     {"id": "md1", "drug": "Ibuprofen 400mg", "dose": "400mg", "freq": "TDS", "duration": "5 days", "instructions": "After food"},
                     {"id": "md2", "drug": "Chlorhexidine Mouthwash 0.2%", "dose": "10ml", "freq": "BD", "duration": "7 days", "instructions": "Rinse 1 min"},
                 ],
                 followup="Analgesia as required. Maintain oral hygiene."),
            tmpl("tpl-5", "Bonding Materials Checklist", "Materials", 87,
                 materials=[
                     {"id": "m1", "name": "Metal Brackets — MBT 0.022", "qty": 20, "unit": "pc", "batch": "BR-2405-092"},
                     {"id": "m2", "name": "Bonding Adhesive", "qty": 1, "unit": "syringe", "batch": "AD-2406-033"},
                 ]),
            tmpl("tpl-6", "Debonding Procedure", "Procedure", 41,
                 procedures=[{"id": "p1", "code": "D8680", "label": "Orthodontic Retention — Removal of Appliances", "teeth": [], "status": "Planned", "duration": "40 min"}],
                 materials=[{"id": "m1", "name": "Retainer — Essix", "qty": 2, "unit": "pc", "batch": "RT-2406-050"}],
                 cc="Debonding and retention",
                 treat="Fixed appliances debonded. Impressions taken for retainers.",
                 followup="Full-time retainer wear for 6 months, then nights only.",
                 disposition="Discharge"),
            tmpl("tpl-7", "Retention Follow-up", "Clinical Notes", 65,
                 cc="Retention review",
                 intra_oral="Alignment stable. Retainer fits well, no distortion.",
                 followup="Continue night-time wear. Review in 6 months."),
            tmpl("tpl-8", "Emergency Pain Protocol", "Medication", 22,
                 diagnoses=[{"id": "d1", "code": "K04.0", "label": "Pulpitis", "primary": True}],
                 medications=[{"id": "md1", "drug": "Ibuprofen 400mg", "dose": "400mg", "freq": "TDS", "duration": "3 days", "instructions": "After food"}],
                 cc="Acute dental pain",
                 diag="Irreversible pulpitis — urgent management required.",
                 followup="Return within 48 hours or sooner if swelling develops.",
                 disposition="Refer"),
        ]
        for t in templates:
            db.add(t)
        db.commit()
        logger.info(f"✅ Seeded {len(templates)} department templates")

        # ──────────────────── Seed a demo Patient Journey ────────────────────
        logger.info("Seeding demo patient journey...")
        try:
            import journey_service
            journey_service.create_journey(
                db,
                created_by_id="u-rec-1",
                patient_id="p-1",
                visit_kind="New",
                steps=[
                    {"doctor_id": "u-doc-1", "step_purpose": "X-Ray"},
                    {"doctor_id": "u-doc-2", "step_purpose": "Consultation"},
                    {"doctor_id": "u-doc-3", "step_purpose": "Braces Fitting"},
                ],
            )
            logger.info("✅ Seeded 1 demo patient journey (3 steps)")
        except Exception as e:  # non-fatal — demo data only
            logger.warning(f"Demo journey not seeded: {e}")

        logger.info("=" * 60)
        logger.info("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Accounts:       {db.query(Account).count()}")
        logger.info(f"Patients:       {db.query(Patient).count()}")
        logger.info(f"Visits:         {db.query(Visit).count()}")
        logger.info(f"Rooms:          {db.query(Room).count()}")
        logger.info(f"Leave Requests: {db.query(LeaveRequest).count()}")
        logger.info(f"Messages:       {db.query(Message).count()}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

