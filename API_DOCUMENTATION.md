"""
AFID Orthodontic HMS - Backend API Documentation

This is a comprehensive backend API for the AFID Orthodontic Hospital Management System.

## Features

- **Authentication**: JWT-based authentication with role-based access control (HOD, Doctor, Reception)
- **Staff Management**: Directory of all personnel with role assignment
- **Patient Management**: Patient records with medical record numbers
- **Visit Scheduling**: Schedule and manage patient visits with doctor and room assignments
- **Room Management**: Treatment room management with capacity tracking
- **Leave Management**: Leave request workflow with HOD approval
- **Messaging**: Direct messages and department-wide channel communication
- **Templates**: Worksheet templates for departments and personal use
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Validation**: Pydantic schemas with comprehensive validation

## Architecture

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration from environment
├── database.py          # SQLAlchemy engine and session
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # JWT token and password utilities
├── services.py          # Business logic layer
├── dependencies.py      # FastAPI dependency injection
├── routes_*.py          # API endpoint handlers
├── seed.py              # Database seeding script
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 13+
- pip or conda

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Database Setup
```bash
# Create PostgreSQL database
createdb afid_hms_db

# Seed initial data
python seed.py
```

### 5. Run Development Server
```bash
python main.py
```

Server runs on `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- Health Check: `http://localhost:8000/health`

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token

### Accounts
- `POST /api/accounts` - Create account (HOD only)
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/me` - Get current user profile
- `GET /api/accounts/{account_id}` - Get account by ID

### Patients
- `POST /api/patients` - Create patient record
- `GET /api/patients` - List all patients
- `GET /api/patients/{patient_id}` - Get patient by ID

### Visits
- `POST /api/visits` - Create patient visit
- `GET /api/visits` - List all visits
- `GET /api/visits/{visit_id}` - Get visit by ID
- `PATCH /api/visits/{visit_id}` - Update visit
- `POST /api/visits/{visit_id}/assign-doctor/{doctor_id}` - Assign doctor to visit
- `POST /api/visits/{visit_id}/assign-room/{room_id}` - Assign room to visit

### Rooms
- `POST /api/rooms` - Create treatment room
- `GET /api/rooms` - List all rooms
- `GET /api/rooms/{room_id}` - Get room by ID
- `PATCH /api/rooms/{room_id}` - Update room
- `POST /api/rooms/{room_id}/assign-doctor/{doctor_id}` - Assign doctor to room

### Leave Requests
- `POST /api/leave` - Submit leave request
- `GET /api/leave` - List leave requests
- `GET /api/leave/my-requests` - Get current user's leave requests
- `GET /api/leave/{leave_id}` - Get leave request by ID
- `POST /api/leave/{leave_id}/decide` - Approve/reject leave (HOD only)

### Messages
- `POST /api/messages` - Send message
- `GET /api/messages/conversation/{conversation_id}` - Get conversation
- `POST /api/messages/{message_id}/read` - Mark message as read

### Templates
- `POST /api/templates` - Create template
- `GET /api/templates` - List templates
- `GET /api/templates/{template_id}` - Get template by ID
- `PATCH /api/templates/{template_id}` - Update template
- `POST /api/templates/{template_id}/use` - Mark template as used

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

### Login Response
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "u-doc-1",
    "name": "Dr. Amna Malik",
    "username": "dr.malik",
    "role": "doctor",
    "title": "Orthodontist · AFID",
    "rank": "Major",
    "dept": "Orthodontics"
  }
}
```

## Example Credentials

Use these credentials to test different roles:

```
HOD:
  username: hod.colonel
  password: hod123

Doctor:
  username: dr.malik
  password: doctor123

Reception:
  username: reception.officer
  password: reception123
```

## Database Models

### Account
Staff directory with authentication.
- id, name, title, rank, dept, initials, status
- username, password_hash, role
- created_at, updated_at, is_seeded

### Patient
Patient medical records.
- id, mr_number (unique), name, rank, doctor_id
- created_at, updated_at

### Visit
Patient visit scheduling and tracking.
- id, patient_id, doctor_id, room_id
- visit_time, visit_type, status, notes
- created_at, updated_at

### Room
Treatment room management.
- id, number (unique), doctor_id, capacity
- patient_count (computed), status (computed)
- created_at, updated_at

### LeaveRequest
Leave request workflow.
- id, requester_id, leave_type, from_date, to_date, reason
- status, decided_by_id, decided_at, decision_note
- created_at, submitted_at, updated_at

### Message
Direct messages and department channel.
- id, conversation_id, sender_id, text
- created_at, read_by (association table)

### Template
Worksheet templates for departments and doctors.
- id, name, template_type, scope, owner_id
- status, usages, last_used
- diagnoses, procedures, medications, investigations, materials
- notes_cc, notes_hpi, notes_extra_oral, notes_intra_oral, notes_diag, notes_treat, notes_followup
- disposition, created_at, updated_at

## Error Handling

API returns standard HTTP status codes:
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include a detail message:
```json
{
  "detail": "Invalid username or password"
}
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong `SECRET_KEY` (minimum 32 characters)
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Use environment-specific database credentials
- [ ] Set up SSL/TLS for HTTPS
- [ ] Configure logging and monitoring
- [ ] Run database migrations
- [ ] Set up automated backups
- [ ] Configure health checks for load balancers

### Docker Deployment
```bash
docker build -t afid-hms-backend .
docker run -p 8000:8000 --env-file .env afid-hms-backend
```

## Development

### Run Tests
```bash
pytest
```

### Generate Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Format Code
```bash
black .
flake8 .
```

## Support

For issues or questions, contact the development team.
"""

# This file serves as comprehensive API documentation
# For interactive API documentation, visit /api/docs after starting the server
