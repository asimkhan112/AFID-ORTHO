"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from database import init_db

# Import routers
from routes_auth import router as auth_router
from routes_accounts import router as accounts_router
from routes_patients import router as patients_router
from routes_visits import router as visits_router
from routes_rooms import router as rooms_router
from routes_leave import router as leave_router
from routes_messages import router as messages_router
from routes_templates import router as templates_router
from routes_export import router as export_router
from routes_journey import router as journey_router

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("🚀 Starting AFID Orthodontic HMS API")
    init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("🛑 Shutting down AFID Orthodontic HMS API")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Let the browser read the download filename on file-export responses.
    expose_headers=["Content-Disposition"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(accounts_router, prefix="/api")
app.include_router(patients_router, prefix="/api")
app.include_router(visits_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(leave_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(journey_router, prefix="/api")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AFID Orthodontic HMS API",
        "version": settings.api_version
    }


# Root endpoint with API documentation
@app.get("/", tags=["Info"])
async def root():
    """API root endpoint with documentation links."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "openapi": "/api/openapi.json",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import os
    import uvicorn
    # Hosting platforms (Railway, Render, Heroku, …) inject the port to bind via
    # the PORT env var; fall back to 8000 for local development.
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
