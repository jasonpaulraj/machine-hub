from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)  # IPv4/IPv6
    mac_address = Column(String(17), nullable=True)  # For Wake-on-LAN
    # Home Assistant entity ID
    ha_entity_id = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    # System info (moved from SystemSnapshot)
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(100), nullable=True)
    hostname = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to snapshots
    snapshots = relationship(
        "SystemSnapshot", back_populates="machine", cascade="all, delete-orphan")


class SystemSnapshot(Base):
    __tablename__ = "system_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)

    # System metrics from Glances
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    memory_used = Column(Float, nullable=True)  # in GB
    memory_total = Column(Float, nullable=True)  # in GB

    uptime = Column(Integer, nullable=True)  # in seconds
    load_avg = Column(Float, nullable=True)

    # Additional CPU metrics
    cpu_user = Column(Float, nullable=True)  # CPU user time %
    cpu_system = Column(Float, nullable=True)  # CPU system time %
    cpu_iowait = Column(Float, nullable=True)  # CPU I/O wait %
    cpu_count = Column(Integer, nullable=True)  # Number of CPU cores

    # Memory swap metrics
    swap_percent = Column(Float, nullable=True)
    swap_used = Column(Float, nullable=True)  # in GB
    swap_total = Column(Float, nullable=True)  # in GB
    swap_free = Column(Float, nullable=True)  # in GB



    # Battery metrics
    battery_percent = Column(Float, nullable=True)
    battery_status = Column(String(20), nullable=True)  # charging, discharging, full

    # JSON data structures for complete sensor/alert/network/filesystem data
    sensors_data = Column(JSON, nullable=True)  # Complete sensors array
    alert_data = Column(JSON, nullable=True)  # Complete alert array
    network_data = Column(JSON, nullable=True)  # Complete network array
    fs_data = Column(JSON, nullable=True)  # Complete filesystem array

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to machine
    machine = relationship("Machine", back_populates="snapshots")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
