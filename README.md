"""Backend project configuration and README."""
# AFID Orthodontic HMS - Backend API

Production-ready FastAPI backend for the AFID Orthodontic Hospital Management System.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Initialize Database
```bash
python seed.py
```

### 4. Run Server
```bash
python main.py
```

Visit `http://localhost:8000/api/docs` for interactive API documentation.

## Project Structure

- **main.py** - FastAPI application entry point
- **config.py** - Configuration management
- **database.py** - Database connection and session management
- **models.py** - SQLAlchemy ORM models
- **schemas.py** - Pydantic request/response schemas
- **auth.py** - Authentication utilities (JWT, password hashing)
- **services.py** - Business logic layer
- **dependencies.py** - FastAPI dependency injection
- **routes_*.py** - API endpoint handlers organized by feature
- **seed.py** - Database initialization with sample data

## Features

✅ JWT-based authentication with role-based access control
✅ SQLAlchemy ORM with PostgreSQL
✅ Pydantic schemas with comprehensive validation
✅ CORS middleware for frontend integration
✅ Comprehensive error handling
✅ Automatic API documentation (Swagger/ReDoc)
✅ Database seeding with sample data
✅ Docker support for easy deployment

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | `postgresql://admin:password@localhost:5432/afid_hms_db` |
| SECRET_KEY | JWT signing key | Auto-generated |
| ALGORITHM | JWT algorithm | `HS256` |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiration time | `30` |
| DEBUG | Enable debug mode | `True` |
| LOG_LEVEL | Logging level | `INFO` |
| ALLOWED_ORIGINS | CORS allowed origins | `http://localhost:3000,http://localhost:5173` |

## API Endpoints Summary

### Auth
- `POST /api/auth/login` - Login

### Accounts (Staff Directory)
- `POST /api/accounts` - Create account
- `GET /api/accounts` - List accounts
- `GET /api/accounts/me` - Current user profile
- `GET /api/accounts/{id}` - Get account

### Patients
- `POST /api/patients` - Create patient
- `GET /api/patients` - List patients
- `GET /api/patients/{id}` - Get patient

### Visits
- `POST /api/visits` - Create visit
- `GET /api/visits` - List visits
- `GET /api/visits/{id}` - Get visit
- `PATCH /api/visits/{id}` - Update visit
- `POST /api/visits/{id}/assign-doctor/{doctor_id}` - Assign doctor
- `POST /api/visits/{id}/assign-room/{room_id}` - Assign room

### Rooms
- `POST /api/rooms` - Create room
- `GET /api/rooms` - List rooms
- `GET /api/rooms/{id}` - Get room
- `PATCH /api/rooms/{id}` - Update room
- `POST /api/rooms/{id}/assign-doctor/{doctor_id}` - Assign doctor

### Leave Requests
- `POST /api/leave` - Submit request
- `GET /api/leave` - List requests
- `GET /api/leave/my-requests` - My requests
- `GET /api/leave/{id}` - Get request
- `POST /api/leave/{id}/decide` - Approve/reject (HOD only)

### Messages
- `POST /api/messages` - Send message
- `GET /api/messages/conversation/{id}` - Get conversation
- `POST /api/messages/{id}/read` - Mark as read

### Templates
- `POST /api/templates` - Create template
- `GET /api/templates` - List templates
- `GET /api/templates/{id}` - Get template
- `PATCH /api/templates/{id}` - Update template
- `POST /api/templates/{id}/use` - Mark as used

## Test Credentials

```
HOD:
  Username: hod.colonel
  Password: hod123

Doctor:
  Username: dr.malik
  Password: doctor123

Reception:
  Username: reception.officer
  Password: reception123
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access API at http://localhost:8000
```

## Development Commands

```bash
# Run with auto-reload
python main.py

# Seed database
python seed.py

# Format code
black .

# Lint code
flake8 .
```

## Database Schema

The backend includes 7 main tables:

1. **account** - Staff directory with authentication
2. **patient** - Patient medical records
3. **visit** - Patient visit scheduling
4. **room** - Treatment room management
5. **leave_request** - Leave request workflow
6. **message** - Direct messages and channels
7. **template** - Worksheet templates

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed documentation.
# AFID-ORTHO
