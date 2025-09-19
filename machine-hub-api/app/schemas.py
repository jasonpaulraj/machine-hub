from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# User schemas


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token schemas


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None

# Machine schemas


class MachineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., min_length=7, max_length=45)
    mac_address: Optional[str] = Field(None, max_length=17)
    ha_entity_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    
    # System info (moved from SystemSnapshot)
    os_name: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=100)


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, min_length=7, max_length=45)
    mac_address: Optional[str] = Field(None, max_length=17)
    ha_entity_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    # System info (moved from SystemSnapshot)
    os_name: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=100)


class Machine(MachineBase):
    id: int
    is_active: bool
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# System snapshot schemas


class SystemSnapshotBase(BaseModel):
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_used: Optional[float] = None
    memory_total: Optional[float] = None

    uptime: Optional[int] = None
    load_avg: Optional[float] = None

    # Additional CPU metrics
    cpu_user: Optional[float] = None
    cpu_system: Optional[float] = None
    cpu_iowait: Optional[float] = None
    cpu_count: Optional[int] = None

    # Memory swap metrics
    swap_percent: Optional[float] = None
    swap_used: Optional[float] = None
    swap_total: Optional[float] = None
    swap_free: Optional[float] = None



    # Battery metrics
    battery_percent: Optional[float] = None
    battery_status: Optional[str] = None

    # JSON data structures
    sensors_data: Optional[List[Dict]] = None  # Complete sensors array
    alert_data: Optional[List[Dict]] = None  # Complete alert array
    network_data: Optional[List[Dict]] = None  # Complete network array
    fs_data: Optional[List[Dict]] = None  # Complete filesystem array

    # Source of the data
    source: Optional[str] = Field(default="api", max_length=20)


class SystemSnapshotCreate(SystemSnapshotBase):
    machine_id: int


class SystemSnapshot(SystemSnapshotBase):
    id: int
    machine_id: int
    created_at: datetime
    source: Optional[str] = Field(default="api", max_length=20)

    class Config:
        from_attributes = True

# Machine with latest snapshot


class MachineWithSnapshot(Machine):
    latest_snapshot: Optional[SystemSnapshot] = None

# Power control schemas


class PowerAction(BaseModel):
    action: str = Field(..., pattern="^(on|off|restart|wake)$")


class PowerResponse(BaseModel):
    success: bool
    message: str
    action: str

# Glances webhook schemas


class GlancesWebhookData(BaseModel):
    hostname: str
    cpu: Optional[dict] = None
    memory: Optional[dict] = None
    disk: Optional[List[dict]] = None
    network: Optional[List[dict]] = None
    uptime: Optional[str] = None
    load: Optional[dict] = None
    system: Optional[dict] = None
    # Allow additional fields

    class Config:
        extra = "allow"

# API Response schemas


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    detail: str
