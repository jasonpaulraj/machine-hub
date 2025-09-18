from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
import asyncio
from dotenv import load_dotenv

from .database import engine
from . import models
from .routers import auth_router, machines_router, webhook_router, polling_router
from .services.glances_poller import start_glances_polling, stop_glances_polling
from .services.cleanup_service import start_cleanup_service, stop_cleanup_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Machine Hub API",
    description="API for controlling and monitoring machines",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth",
                   tags=["authentication"])
app.include_router(machines_router.router,
                   prefix="/api/machines", tags=["machines"])
app.include_router(webhook_router.router, prefix="/webhook", tags=["webhooks"])
app.include_router(polling_router.router,
                   prefix="/api/polling", tags=["polling"])


@app.on_event("startup")
async def startup_event():
    # Start Glances polling service in background
    asyncio.create_task(start_glances_polling())
    # Start cleanup service
    asyncio.create_task(start_cleanup_service())


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("⏹️ Shutting down Machine Hub API")
    stop_glances_polling()
    stop_cleanup_service()


@app.get("/")
async def root():
    return {"message": "Machine Hub API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
