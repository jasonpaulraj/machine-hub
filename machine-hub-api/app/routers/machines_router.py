from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from .. import crud, schemas, auth
from ..ha_integration import power_on_machine, power_off_machine, get_machine_power_state
from ..wol import wake_machine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[schemas.Machine])
async def get_machines(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of machines"""
    machines = crud.get_machines(
        db, skip=skip, limit=limit, active_only=active_only)
    return machines


@router.get("/with-snapshots")
async def get_machines_with_snapshots(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get machines with their latest system snapshots"""
    machines_data = crud.get_machines_with_latest_snapshots(
        db, skip=skip, limit=limit, active_only=active_only)

    result = []
    for item in machines_data:
        machine_dict = {
            "id": item["machine"].id,
            "name": item["machine"].name,
            "hostname": item["machine"].hostname,
            "ip_address": item["machine"].ip_address,
            "mac_address": item["machine"].mac_address,
            "ha_entity_id": item["machine"].ha_entity_id,
            "description": item["machine"].description,
            "is_active": item["machine"].is_active,
            "last_seen": item["machine"].last_seen,
            "os_name": item["machine"].os_name,
            "os_version": item["machine"].os_version,
            "created_at": item["machine"].created_at,
            "updated_at": item["machine"].updated_at,
            "latest_snapshot": item["latest_snapshot"]
        }
        result.append(machine_dict)

    return result


@router.get("/{machine_id}", response_model=schemas.Machine)
async def get_machine(
    machine_id: int,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific machine by ID"""
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.post("/", response_model=schemas.Machine)
async def create_machine(
    machine: schemas.MachineCreate,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new machine"""
    logger.info(
        f"User {current_user.username} attempting to add new machine: {machine.name} ({machine.hostname})")

    # Check if machine with same hostname or IP already exists
    existing_hostname = crud.get_machine_by_hostname(
        db, hostname=machine.hostname)
    if existing_hostname:
        logger.warning(
            f"Machine creation failed - hostname {machine.hostname} already exists")
        raise HTTPException(
            status_code=400,
            detail="Machine with this hostname already exists"
        )

    existing_ip = crud.get_machine_by_ip(db, ip_address=machine.ip_address)
    if existing_ip:
        logger.warning(
            f"Machine creation failed - IP address {machine.ip_address} already exists")
        raise HTTPException(
            status_code=400,
            detail="Machine with this IP address already exists"
        )

    new_machine = crud.create_machine(db=db, machine=machine)
    logger.info(
        f"Successfully added new machine: {new_machine.name} (ID: {new_machine.id}, IP: {new_machine.ip_address}) by user {current_user.username}")

    return new_machine


@router.put("/{machine_id}", response_model=schemas.Machine)
async def update_machine(
    machine_id: int,
    machine_update: schemas.MachineUpdate,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a machine"""
    machine = crud.update_machine(
        db, machine_id=machine_id, machine_update=machine_update)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.delete("/{machine_id}")
async def delete_machine(
    machine_id: int,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a machine"""
    success = crud.delete_machine(db, machine_id=machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Machine deleted successfully"}


@router.post("/{machine_id}/power", response_model=schemas.PowerResponse)
async def control_machine_power(
    machine_id: int,
    power_action: schemas.PowerAction,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Control machine power (on/off/restart)"""
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    if power_action.action == "on":
        result = power_on_machine(machine)
    elif power_action.action == "off":
        result = power_off_machine(machine)
    elif power_action.action == "restart":
        # First turn off, then turn on after a delay
        off_result = power_off_machine(machine)
        if off_result["success"]:
            import time
            time.sleep(2)  # Wait 2 seconds
            result = power_on_machine(machine)
            result["message"] = f"Restart initiated for {machine.name}"
        else:
            result = off_result
    elif power_action.action == "wake":
        result = wake_machine(machine)
    else:
        raise HTTPException(status_code=400, detail="Invalid power action")

    return schemas.PowerResponse(
        success=result["success"],
        message=result["message"],
        action=power_action.action
    )


@router.get("/{machine_id}/power-state")
async def get_machine_power_state_endpoint(
    machine_id: int,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current power state of a machine"""
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    result = get_machine_power_state(machine)
    return result


@router.get("/{machine_id}/snapshots", response_model=List[schemas.SystemSnapshot])
async def get_machine_snapshots(
    machine_id: int,
    limit: int = Query(default=100, le=1000),
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system snapshots for a machine"""
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    snapshots = crud.get_machine_snapshots(
        db, machine_id=machine_id, limit=limit)
    return snapshots


@router.get("/{machine_id}/snapshots/latest", response_model=Optional[schemas.SystemSnapshot])
async def get_latest_machine_snapshot(
    machine_id: int,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the latest system snapshot for a machine"""
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    snapshot = crud.get_latest_snapshot(db, machine_id=machine_id)
    return snapshot


@router.get("/{machine_id}/snapshots/timerange", response_model=List[schemas.SystemSnapshot])
async def get_machine_snapshots_timerange(
    machine_id: int,
    start_time: datetime,
    end_time: datetime,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system snapshots for a machine within a time range"""
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    snapshots = crud.get_snapshots_in_timerange(
        db, machine_id=machine_id, start_time=start_time, end_time=end_time)
    return snapshots
