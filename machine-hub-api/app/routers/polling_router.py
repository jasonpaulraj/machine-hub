from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import logging

from ..database import get_db
from ..auth import verify_api_key
from ..services.glances_poller import glances_poller
from .. import schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/trigger-collection")
async def trigger_data_collection(
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Manually trigger data collection from all active machines
    """
    try:
        logger.info("🔄 Manual data collection triggered")

        # Trigger immediate polling of all machines
        await glances_poller.poll_all_machines()

        return schemas.APIResponse(
            success=True,
            message="Data collection completed successfully",
            data={"status": "completed"}
        )

    except Exception as e:
        logger.error(f"Error during manual data collection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect data: {str(e)}"
        )


@router.get("/polling-status")
async def get_polling_status(
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get the current status of the polling service
    """
    return schemas.APIResponse(
        success=True,
        message="Polling status retrieved",
        data={
            "running": glances_poller.running,
            "poll_interval": glances_poller.poll_interval
        }
    )


@router.post("/start-polling")
async def start_polling(
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Start the polling service if it's not running
    """
    if glances_poller.running:
        return schemas.APIResponse(
            success=True,
            message="Polling service is already running",
            data={"status": "already_running"}
        )

    try:
        # Start polling in background
        asyncio.create_task(glances_poller.start_polling())

        return schemas.APIResponse(
            success=True,
            message="Polling service started",
            data={"status": "started"}
        )

    except Exception as e:
        logger.error(f"Error starting polling service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start polling: {str(e)}"
        )


@router.post("/stop-polling")
async def stop_polling(
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Stop the polling service
    """
    if not glances_poller.running:
        return schemas.APIResponse(
            success=True,
            message="Polling service is not running",
            data={"status": "not_running"}
        )

    try:
        glances_poller.stop_polling()

        return schemas.APIResponse(
            success=True,
            message="Polling service stopped",
            data={"status": "stopped"}
        )

    except Exception as e:
        logger.error(f"Error stopping polling service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop polling: {str(e)}"
        )
