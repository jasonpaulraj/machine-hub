import asyncio
import aiohttp
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas
from ..models import Machine

logger = logging.getLogger(__name__)

def should_log():
    """Check if logging should be enabled based on environment"""
    return os.getenv('APP_ENV', '').lower() != 'production'


class GlancesPoller:
    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval
        self.session_timeout = aiohttp.ClientTimeout(total=10)
        self.running = False

    async def start_polling(self):
        """Start the polling loop"""
        self.running = True
        if should_log():
            logger.info("🔄 Starting Glances polling service")

        while self.running:
            try:
                await self.poll_all_machines()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                if should_log():
                    logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry

    def stop_polling(self):
        """Stop the polling loop"""
        self.running = False
        if should_log():
            logger.info("⏹️ Stopping Glances polling service")

    async def poll_all_machines(self):
        """Poll all active machines for metrics"""
        db = next(get_db())
        try:
            machines = crud.get_active_machines(db)
            if not machines:
                if should_log():
                    logger.debug("No active machines to poll")
                return

            if should_log():
                logger.info(f"📊 Polling {len(machines)} machines for metrics")

            # Create tasks for concurrent polling
            tasks = []
            for machine in machines:
                task = asyncio.create_task(self.poll_machine(db, machine))
                tasks.append(task)

            # Wait for all polling tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            if should_log():
                logger.error(f"Error polling machines: {e}")
        finally:
            db.close()

    async def poll_machine(self, db: Session, machine: Machine):
        """Poll a single machine for Glances data"""
        try:
            glances_url = f"http://{machine.ip_address}:61208/api/4/all"
            if should_log():
                logger.info(
                    f"🔗 Attempting to poll {machine.name} at {glances_url}")

            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(glances_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if should_log():
                            logger.info(
                                f"✅ Successfully connected to {machine.name}, processing data...")
                        await self.process_glances_data(db, machine, data)

                        # Update last_seen timestamp
                        crud.update_machine_last_seen(db, machine.id)

                        if should_log():
                            logger.info(f"✅ Successfully polled {machine.name}")
                    else:
                        if should_log():
                            logger.warning(
                                f"❌ Failed to poll {machine.name}: HTTP {response.status}")

        except asyncio.TimeoutError:
            if should_log():
                logger.warning(
                    f"⏰ Timeout polling {machine.name} at {machine.ip_address}")
        except aiohttp.ClientError as e:
            if should_log():
                logger.warning(f"🔌 Connection error polling {machine.name}: {e}")
        except Exception as e:
            if should_log():
                logger.error(f"💥 Unexpected error polling {machine.name}: {e}")

    async def process_glances_data(self, db: Session, machine: Machine, data: Dict[str, Any]):
        """Process and store Glances data for a machine"""
        try:
            # Debug: Log the keys we receive from Glances API
            # logger.info(f"🔍 Polling received data keys: {list(data.keys())}")

            parsed_data = self.parse_glances_data(data)

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
                fs_data=parsed_data.get("fs_data"),
                # Source identifier
                source="api"
            )

            # Store in database
            crud.create_system_snapshot(db, snapshot_data)
            if should_log():
                logger.debug(f"💾 Stored snapshot for {machine.name}")

        except Exception as e:
            if should_log():
                logger.error(f"Error processing data for {machine.name}: {e}")

    def parse_glances_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

        # Parse disk data (use root filesystem)
        if "fs" in data and isinstance(data["fs"], list) and len(data["fs"]) > 0:
            # Find root filesystem or use first one
            root_fs = None
            for fs in data["fs"]:
                if fs.get("mnt_point") == "/":
                    root_fs = fs
                    break
            if not root_fs and data["fs"]:
                root_fs = data["fs"][0]  # Use first filesystem as fallback

            if root_fs:
                pass  # Disk data now available through fs_data JSON

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
                if should_log():
                    logger.warning(f"Failed to parse uptime '{uptime_raw}': {e}")
                parsed["uptime"] = 0
        else:
            parsed["uptime"] = int(uptime_raw) if uptime_raw else 0

        # Parse load average
        if "load" in data and isinstance(data["load"], dict):
            parsed["load_avg"] = data["load"].get(
                "min1")  # 1-minute load average

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
                        parsed["battery_percent"] = float(
                            sensor.get("value", 0))
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


# Global poller instance
glances_poller = GlancesPoller(poll_interval=30)  # Poll every 30 seconds


async def start_glances_polling():
    """Start the Glances polling service"""
    await glances_poller.start_polling()


def stop_glances_polling():
    """Stop the Glances polling service"""
    glances_poller.stop_polling()
