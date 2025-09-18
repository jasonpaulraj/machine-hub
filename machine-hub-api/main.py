from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from app.database import engine, Base
from app.routers import auth_router, machines_router, webhook_router
from app import crud
from app.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Machine Hub API...")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create default admin user if it doesn't exist
        db = next(get_db())
        try:
            admin_user = crud.get_user_by_username(db, "admin")
            if not admin_user:
                admin_data = {
                    "username": "admin",
                    "email": "admin@localhost",
                    "password": "admin123",
                    "is_admin": True
                }
                crud.create_user(db, admin_data)
                logger.info(
                    "Default admin user created (username: admin, password: admin123)")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Machine Hub API...")

# Create FastAPI app
app = FastAPI(
    title="Machine Hub API",
    description="API for managing and monitoring machines with Home Assistant integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://machine-hub-web:3000",  # Docker container
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth",
                   tags=["authentication"])
app.include_router(machines_router.router,
                   prefix="/api/machines", tags=["machines"])
app.include_router(webhook_router.router,
                   prefix="/api/webhook", tags=["webhooks"])

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Machine Hub API",
        "version": "1.0.0"
    }

# Root endpoint


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Machine Hub API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Global exception handler


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
