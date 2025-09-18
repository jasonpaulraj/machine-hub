#!/usr/bin/env python3
"""
Cleanup Service for System Snapshots

This service automatically maintains the database by keeping only the latest
10000 records per machine and optionally cleaning up old records by age.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import sessionmaker
from ..database import engine
from .. import crud

logger = logging.getLogger(__name__)


def should_log():
    """Check if logging should be enabled based on environment"""
    return os.getenv('APP_ENV', '').lower() != 'production'


class CleanupService:
    """Background service for database cleanup tasks"""

    def __init__(self,
                 max_records_per_machine: int = 10000,
                 cleanup_interval_hours: int = 6,
                 cleanup_old_records_days: Optional[int] = None):
        """
        Initialize cleanup service

        Args:
            max_records_per_machine: Maximum number of records to keep per machine
            cleanup_interval_hours: How often to run cleanup (in hours)
            cleanup_old_records_days: If set, also cleanup records older than N days
        """
        self.max_records_per_machine = max_records_per_machine
        self.cleanup_interval_hours = cleanup_interval_hours
        self.cleanup_old_records_days = cleanup_old_records_days
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

        # Create database session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)

    async def start(self):
        """Start the cleanup service"""
        if self.is_running:
            if should_log():
                logger.warning("Cleanup service is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._cleanup_loop())
        if should_log():
            logger.info(
                f"🧹 Cleanup service started - will run every {self.cleanup_interval_hours} hours")
            logger.info(
                f"📊 Keeping latest {self.max_records_per_machine} records per machine")
            if self.cleanup_old_records_days:
                logger.info(
                    f"🗓️ Also removing records older than {self.cleanup_old_records_days} days")

    async def stop(self):
        """Stop the cleanup service"""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if should_log():
            logger.info("🛑 Cleanup service stopped")

    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.is_running:
            try:
                await self._run_cleanup()

                # Wait for next cleanup interval
                # Convert hours to seconds
                await asyncio.sleep(self.cleanup_interval_hours * 3600)

            except asyncio.CancelledError:
                if should_log():
                    logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                if should_log():
                    logger.error(f"Error in cleanup loop: {e}")
                # Wait a bit before retrying on error
                await asyncio.sleep(300)  # 5 minutes

    async def _run_cleanup(self):
        """Run the actual cleanup operations"""
        if should_log():
            logger.info("🧹 Starting database cleanup...")

        db = self.SessionLocal()
        try:
            total_deleted = 0

            # Cleanup by count (keep latest N records per machine)
            deleted_by_count = crud.cleanup_snapshots_by_count(
                db, max_records_per_machine=self.max_records_per_machine
            )
            total_deleted += deleted_by_count

            if deleted_by_count > 0 and should_log():
                logger.info(
                    f"📊 Deleted {deleted_by_count} records to maintain {self.max_records_per_machine} records per machine")

            # Cleanup by age (if configured)
            if self.cleanup_old_records_days:
                deleted_by_age = crud.cleanup_old_snapshots(
                    db, days_to_keep=self.cleanup_old_records_days
                )
                total_deleted += deleted_by_age

                if deleted_by_age > 0 and should_log():
                    logger.info(
                        f"🗓️ Deleted {deleted_by_age} records older than {self.cleanup_old_records_days} days")

            if total_deleted == 0:
                if should_log():
                    logger.debug(
                        "✅ No cleanup needed - database is within limits")
            else:
                if should_log():
                    logger.info(
                        f"✅ Cleanup completed - total {total_deleted} records deleted")

        except Exception as e:
            if should_log():
                logger.error(f"Error during cleanup: {e}")
            db.rollback()
        finally:
            db.close()

    async def run_cleanup_now(self) -> dict:
        """Run cleanup immediately and return results"""
        if should_log():
            logger.info("🧹 Running immediate cleanup...")

        db = self.SessionLocal()
        try:
            results = {
                "deleted_by_count": 0,
                "deleted_by_age": 0,
                "total_deleted": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Cleanup by count
            deleted_by_count = crud.cleanup_snapshots_by_count(
                db, max_records_per_machine=self.max_records_per_machine
            )
            results["deleted_by_count"] = deleted_by_count

            # Cleanup by age (if configured)
            if self.cleanup_old_records_days:
                deleted_by_age = crud.cleanup_old_snapshots(
                    db, days_to_keep=self.cleanup_old_records_days
                )
                results["deleted_by_age"] = deleted_by_age

            results["total_deleted"] = deleted_by_count + \
                results["deleted_by_age"]

            if should_log():
                logger.info(
                    f"✅ Immediate cleanup completed - {results['total_deleted']} records deleted")
            return results

        except Exception as e:
            if should_log():
                logger.error(f"Error during immediate cleanup: {e}")
            db.rollback()
            raise
        finally:
            db.close()


# Global cleanup service instance
cleanup_service: Optional[CleanupService] = None


def get_cleanup_service() -> CleanupService:
    """Get or create the global cleanup service instance"""
    global cleanup_service
    if cleanup_service is None:
        cleanup_service = CleanupService(
            max_records_per_machine=10000,  # Keep latest 10000 records per machine
            cleanup_interval_hours=6,       # Run every 6 hours
            cleanup_old_records_days=None   # Don't cleanup by age (optional)
        )
    return cleanup_service


async def start_cleanup_service():
    """Start the global cleanup service"""
    service = get_cleanup_service()
    await service.start()


async def stop_cleanup_service():
    """Stop the global cleanup service"""
    global cleanup_service
    if cleanup_service:
        await cleanup_service.stop()
