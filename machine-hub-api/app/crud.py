from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional, List
from datetime import datetime, timedelta

from . import models, schemas
from .auth import hash_password

# User CRUD operations


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = hash_password(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

# Machine CRUD operations


def get_machine(db: Session, machine_id: int) -> Optional[models.Machine]:
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()


def get_machine_by_hostname(db: Session, hostname: str) -> Optional[models.Machine]:
    return db.query(models.Machine).filter(models.Machine.hostname == hostname).first()


def get_machine_by_ip(db: Session, ip_address: str) -> Optional[models.Machine]:
    return db.query(models.Machine).filter(models.Machine.ip_address == ip_address).first()


def get_machines(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[models.Machine]:
    query = db.query(models.Machine)
    if active_only:
        query = query.filter(models.Machine.is_active == True)
    return query.offset(skip).limit(limit).all()


def get_active_machines(db: Session) -> List[models.Machine]:
    """Get all active machines for polling"""
    return db.query(models.Machine).filter(models.Machine.is_active == True).all()


def create_machine(db: Session, machine: schemas.MachineCreate) -> models.Machine:
    db_machine = models.Machine(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine


def update_machine(db: Session, machine_id: int, machine_update: schemas.MachineUpdate) -> Optional[models.Machine]:
    db_machine = get_machine(db, machine_id)
    if not db_machine:
        return None

    update_data = machine_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_machine, field, value)

    db.commit()
    db.refresh(db_machine)
    return db_machine


def delete_machine(db: Session, machine_id: int) -> bool:
    db_machine = get_machine(db, machine_id)
    if not db_machine:
        return False

    db.delete(db_machine)
    db.commit()
    return True


def update_machine_last_seen(db: Session, machine_id: int) -> Optional[models.Machine]:
    db_machine = get_machine(db, machine_id)
    if not db_machine:
        return None

    db_machine.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(db_machine)
    return db_machine

# System snapshot CRUD operations


def create_system_snapshot(db: Session, snapshot: schemas.SystemSnapshotCreate) -> models.SystemSnapshot:
    db_snapshot = models.SystemSnapshot(**snapshot.dict())
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)

    # Update machine's last_seen timestamp
    update_machine_last_seen(db, snapshot.machine_id)

    return db_snapshot


def get_latest_snapshot(db: Session, machine_id: int) -> Optional[models.SystemSnapshot]:
    return db.query(models.SystemSnapshot).filter(
        models.SystemSnapshot.machine_id == machine_id
    ).order_by(desc(models.SystemSnapshot.created_at)).first()


def get_machine_snapshots(db: Session, machine_id: int, limit: int = 100) -> List[models.SystemSnapshot]:
    return db.query(models.SystemSnapshot).filter(
        models.SystemSnapshot.machine_id == machine_id
    ).order_by(desc(models.SystemSnapshot.created_at)).limit(limit).all()


def get_snapshots_in_timerange(db: Session, machine_id: int, start_time: datetime, end_time: datetime) -> List[models.SystemSnapshot]:
    return db.query(models.SystemSnapshot).filter(
        and_(
            models.SystemSnapshot.machine_id == machine_id,
            models.SystemSnapshot.created_at >= start_time,
            models.SystemSnapshot.created_at <= end_time
        )
    ).order_by(desc(models.SystemSnapshot.created_at)).all()


def cleanup_old_snapshots(db: Session, days_to_keep: int = 30) -> int:
    """Remove snapshots older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    deleted_count = db.query(models.SystemSnapshot).filter(
        models.SystemSnapshot.created_at < cutoff_date
    ).delete()
    db.commit()
    return deleted_count


def cleanup_snapshots_by_count(db: Session, max_records_per_machine: int = 10000) -> int:
    """Keep only the latest N records per machine, delete older ones"""
    total_deleted = 0

    # Get all machines
    machines = db.query(models.Machine).all()

    for machine in machines:
        # Count total snapshots for this machine
        total_snapshots = db.query(models.SystemSnapshot).filter(
            models.SystemSnapshot.machine_id == machine.id
        ).count()

        if total_snapshots > max_records_per_machine:
            # Get the IDs of snapshots to delete (oldest ones)
            snapshots_to_delete = db.query(models.SystemSnapshot.id).filter(
                models.SystemSnapshot.machine_id == machine.id
            ).order_by(desc(models.SystemSnapshot.created_at)).offset(max_records_per_machine).all()

            if snapshots_to_delete:
                # Extract just the IDs
                snapshot_ids = [
                    snapshot.id for snapshot in snapshots_to_delete]

                # Delete the old snapshots
                deleted_count = db.query(models.SystemSnapshot).filter(
                    models.SystemSnapshot.id.in_(snapshot_ids)
                ).delete(synchronize_session=False)

                total_deleted += deleted_count

    db.commit()
    return total_deleted

# Helper functions


def get_machines_with_latest_snapshots(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[dict]:
    """Get machines with their latest system snapshots"""
    machines = get_machines(db, skip, limit, active_only)
    result = []

    for machine in machines:
        latest_snapshot = get_latest_snapshot(db, machine.id)
        machine_dict = {
            "machine": machine,
            "latest_snapshot": latest_snapshot
        }
        result.append(machine_dict)

    return result
