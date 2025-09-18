from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime

from ..database import get_db
from .. import crud, schemas
from ..auth import verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_glances_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Glances data and extract relevant metrics"""
    # Extract hostname from system data or fallback to root level
    hostname = "unknown"
    if "system" in data and isinstance(data["system"], dict):
        hostname = data["system"].get("hostname", "unknown")
    else:
        hostname = data.get("hostname", "unknown")

    parsed = {
        "hostname": hostname,
        "cpu_percent": None,
        "memory_percent": None,
        "memory_used": None,
        "memory_total": None,

        "uptime": None,
        "load_avg": None,
        "os_name": None,
        "os_version": None,
        # Additional CPU metrics
        "cpu_user": None,
        "cpu_system": None,
        "cpu_iowait": None,
        "cpu_count": None,
        # Memory swap metrics
        "swap_percent": None,
        "swap_used": None,
        "swap_total": None,
        "swap_free": None,

        # Battery metrics
        "battery_percent": None,
        "battery_status": None,
        # Filesystem data
        "fs_data": None
    }

    # Parse CPU data
    if "cpu" in data and isinstance(data["cpu"], dict):
        cpu_data = data["cpu"]
        parsed["cpu_percent"] = cpu_data.get("total")
        parsed["cpu_user"] = cpu_data.get("user")
        parsed["cpu_system"] = cpu_data.get("system")
        parsed["cpu_iowait"] = cpu_data.get("iowait")
        if "cpucore" in cpu_data and isinstance(cpu_data["cpucore"], (list, dict)):
            parsed["cpu_count"] = len(cpu_data["cpucore"])
        elif "cpucore" in cpu_data and isinstance(cpu_data["cpucore"], int):
            parsed["cpu_count"] = cpu_data["cpucore"]

    # Parse memory data
    if "mem" in data and isinstance(data["mem"], dict):
        mem_data = data["mem"]
        parsed["memory_percent"] = mem_data.get("percent")
        if "used" in mem_data:
            parsed["memory_used"] = mem_data["used"] / \
                (1024**3)  # Convert to GB
        if "total" in mem_data:
            parsed["memory_total"] = mem_data["total"] / \
                (1024**3)  # Convert to GB

    # Parse memory swap data
    if "memswap" in data and isinstance(data["memswap"], dict):
        swap_data = data["memswap"]
        parsed["swap_percent"] = swap_data.get("percent")
        if "used" in swap_data:
            parsed["swap_used"] = float(
                swap_data["used"]) / (1024**3)  # Convert to GB
        if "total" in swap_data:
            parsed["swap_total"] = float(
                swap_data["total"]) / (1024**3)  # Convert to GB
        if "free" in swap_data:
            parsed["swap_free"] = float(
                swap_data["free"]) / (1024**3)  # Convert to GB

    # Parse uptime (convert to seconds if it's a string)
    uptime_raw = data.get('uptime', 0)
    if isinstance(uptime_raw, str):
        # Parse uptime string like "30 days, 17:37:37" to seconds
        try:
            import re
            # Extract days, hours, minutes, seconds
            days_match = re.search(r'(\d+)\s+days?', uptime_raw)
            time_match = re.search(r'(\d+):(\d+):(\d+)', uptime_raw)

            days = int(days_match.group(1)) if days_match else 0
            hours = int(time_match.group(1)) if time_match else 0
            minutes = int(time_match.group(2)) if time_match else 0
            seconds = int(time_match.group(3)) if time_match else 0

            parsed["uptime"] = days * 86400 + \
                hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            logger.warning(f"Failed to parse uptime '{uptime_raw}': {e}")
            parsed["uptime"] = 0
    else:
        parsed["uptime"] = int(uptime_raw) if uptime_raw else 0

    # Parse load average
    if "load" in data and isinstance(data["load"], dict):
        parsed["load_avg"] = data["load"].get("min1")  # 1-minute load average

    # Parse system info
    if "system" in data and isinstance(data["system"], dict):
        system_data = data["system"]
        parsed["os_name"] = system_data.get("os_name")
        parsed["os_version"] = system_data.get("os_version")

    # Parse battery data
    if "sensors" in data and isinstance(data["sensors"], list):
        for sensor in data["sensors"]:
            if isinstance(sensor, dict) and sensor.get("label") == "Battery":
                if "value" in sensor:
                    parsed["battery_percent"] = float(sensor.get("value", 0))
                if "status" in sensor:
                    parsed["battery_status"] = str(sensor.get("status"))

    # Parse filesystem data
    if "fs" in data and isinstance(data["fs"], list):
        parsed["fs_data"] = data["fs"]

    # Store complete JSON data structures
    if "sensors" in data:
        if isinstance(data["sensors"], list):
            parsed["sensors_data"] = data["sensors"]
        else:
            # Store string values (like "Not available") as well
            parsed["sensors_data"] = data["sensors"]

    if "alert" in data:
        if isinstance(data["alert"], list):
            parsed["alert_data"] = data["alert"]
        else:
            # Store string values (like "Not available") as well
            parsed["alert_data"] = data["alert"]

    if "network" in data and isinstance(data["network"], list):
        parsed["network_data"] = data["network"]

    return parsed


@router.post("/glances")
async def receive_glances_data(
    request: Request,
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Receive system metrics data from Glances"""

    # Verify API key if configured
    if not verify_api_key(x_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

    # Parse the request body
    try:
        raw_data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )

    # Get client IPs from payload
    external_ip = raw_data.get('external_ip')
    local_ip = raw_data.get('local_ip')

    # Collect all available IPs to check
    ips_to_check = [ip for ip in [external_ip, local_ip] if ip]

    if not ips_to_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing IP information in request payload"
        )

    # Check if any of the client IPs are registered in machines table
    allowed_machine = None
    matched_ip = None

    for ip in ips_to_check:
        machine = crud.get_machine_by_ip(db, ip_address=ip)
        if machine:
            allowed_machine = machine
            matched_ip = ip
            break

    if not allowed_machine:
        logger.warning(
            f"Webhook access denied for unregistered IPs: {ips_to_check}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: None of the provided IPs {ips_to_check} are registered in machines table"
        )

    # Use the matched IP for logging
    client_ip = matched_ip

    try:

        # Parse the data
        parsed_data = parse_glances_data(raw_data)
        hostname = parsed_data["hostname"]

        # Find machine by hostname
        machine = crud.get_machine_by_hostname(db, hostname=hostname)
        if not machine:
            # Use the IP-validated machine if hostname doesn't match
            machine = allowed_machine

        if not machine:
            logger.warning(
                f"Received Glances data for unknown machine: {hostname} (IP: {client_ip})")
            return {
                "success": False,
                "message": f"Machine not found: {hostname}",
                "hostname": hostname
            }

        # Update machine system info if empty or different
        machine_updated = False
        os_name = parsed_data.get("os_name")
        os_version = parsed_data.get("os_version")
        hostname = parsed_data.get("hostname")

        if os_name and (not machine.os_name or machine.os_name != os_name):
            machine.os_name = os_name
            machine_updated = True

        if os_version and (not machine.os_version or machine.os_version != os_version):
            machine.os_version = os_version
            machine_updated = True

        if hostname and (not machine.hostname or machine.hostname != hostname):
            machine.hostname = hostname
            machine_updated = True

        if machine_updated:
            db.commit()
            db.refresh(machine)

        # Create snapshot record with all metrics
        snapshot_data = schemas.SystemSnapshotCreate(
            machine_id=machine.id,
            cpu_percent=parsed_data.get("cpu_percent"),
            memory_percent=parsed_data.get("memory_percent"),
            memory_used=parsed_data.get("memory_used"),
            memory_total=parsed_data.get("memory_total"),

            uptime=parsed_data.get("uptime"),
            load_avg=parsed_data.get("load_avg"),
            # Additional CPU metrics
            cpu_user=parsed_data.get("cpu_user"),
            cpu_system=parsed_data.get("cpu_system"),
            cpu_iowait=parsed_data.get("cpu_iowait"),
            cpu_count=parsed_data.get("cpu_count"),
            # Memory swap metrics
            swap_percent=parsed_data.get("swap_percent"),
            swap_used=parsed_data.get("swap_used"),
            swap_total=parsed_data.get("swap_total"),
            swap_free=parsed_data.get("swap_free"),

            # Battery metrics
            battery_percent=parsed_data.get("battery_percent"),
            battery_status=parsed_data.get("battery_status"),
            # JSON data structures
            sensors_data=parsed_data.get("sensors_data"),
            alert_data=parsed_data.get("alert_data"),
            network_data=parsed_data.get("network_data"),
            fs_data=parsed_data.get("fs_data")
        )

        # Store in database
        snapshot = crud.create_system_snapshot(db, snapshot_data)

        # Update last_seen timestamp
        crud.update_machine_last_seen(db, machine.id)

        logger.info(
            f"📊 Metrics collected for machine '{machine.name}' (ID: {machine.id}) - CPU: {parsed_data.get('cpu_percent')}%, Memory: {parsed_data.get('memory_percent')}%")

        return {
            "success": True,
            "message": "Data received and stored successfully",
            "machine_id": machine.id,
            "machine_name": machine.name,
            "snapshot_id": snapshot.id
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON data"
        )
    except Exception as e:
        logger.error(f"Error processing Glances webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook data"
        )


@router.get("/glances/test")
async def test_glances_webhook():
    """Test endpoint for Glances webhook"""
    return {
        "message": "Glances webhook endpoint is working",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/webhook/glances"
    }


@router.post("/cleanup-snapshots")
async def cleanup_old_snapshots(
    days_to_keep: int = 30,
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Clean up old system snapshots by age (admin endpoint)"""

    # Verify API key
    if not verify_api_key(x_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

    try:
        deleted_count = crud.cleanup_old_snapshots(
            db, days_to_keep=days_to_keep)
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old snapshots",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
            "cleanup_method": "by_age"
        }
    except Exception as e:
        logger.error(f"Error cleaning up snapshots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cleaning up snapshots"
        )


@router.post("/cleanup-snapshots-by-count")
async def cleanup_snapshots_by_count(
    max_records_per_machine: int = 10000,
    x_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Keep only the latest N records per machine, delete older ones (admin endpoint)"""

    # Verify API key
    if not verify_api_key(x_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

    try:
        deleted_count = crud.cleanup_snapshots_by_count(
            db, max_records_per_machine=max_records_per_machine)
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old snapshots, keeping latest {max_records_per_machine} per machine",
            "deleted_count": deleted_count,
            "max_records_per_machine": max_records_per_machine,
            "cleanup_method": "by_count"
        }
    except Exception as e:
        logger.error(f"Error cleaning up snapshots by count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cleaning up snapshots"
        )
