# ORM models for the RepairHub application.
# Defines Customer, Device, Job, JobStatusLog, and Payment tables.
# Also defines allowed status values and valid status transitions.

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Text, JSON,
)
from sqlalchemy.orm import relationship
from database.db import Base

# All possible job status values in workflow order
STATUS_LIST = [
    "Received", "Under Inspection", "In Repair", "Waiting for Parts",
    "Testing", "Ready", "Delivered", "Cancelled",
]

# Defines which status transitions are permitted for each current status
VALID_TRANSITIONS: dict[str, list[str]] = {
    status: [s for s in STATUS_LIST if s != status]
    for status in STATUS_LIST
}


class Customer(Base):
    """Represents a customer who brings in devices for repair."""
    __tablename__ = "customers"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(100), nullable=False)
    phone      = Column(String(20),  nullable=False, unique=True)
    email      = Column(String(100), default="")
    address    = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    # One customer can have many devices and jobs
    devices    = relationship("Device",  back_populates="customer", cascade="all, delete-orphan", lazy="select")
    jobs       = relationship("Job",     back_populates="customer", cascade="all, delete-orphan")


class Device(Base):
    """Represents a physical device brought in by a customer."""
    __tablename__ = "devices"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    customer_id  = Column(Integer, ForeignKey("customers.id"), nullable=False)
    brand        = Column(String(60),  nullable=False)
    model        = Column(String(100), nullable=False)
    serial_no    = Column(String(100), default="")
    imei         = Column(String(20),  default="")
    problem_desc = Column(Text, nullable=False)
    entry_date   = Column(DateTime, default=datetime.now)
    image_paths  = Column(JSON, default=list)  # List of image file paths
    customer     = relationship("Customer", back_populates="devices", lazy="joined")
    jobs         = relationship("Job", back_populates="device", cascade="all, delete-orphan")


class Job(Base):
    """Represents a repair work order linked to a device and customer."""
    __tablename__ = "jobs"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    device_id   = Column(Integer, ForeignKey("devices.id"),   nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status      = Column(String(30), nullable=False, default="Received")
    notes       = Column(Text, default="")
    technician  = Column(String(100), default="")
    created_at  = Column(DateTime, default=datetime.now)
    updated_at  = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    device      = relationship("Device",       back_populates="jobs",        lazy="joined")
    customer    = relationship("Customer",     back_populates="jobs",        lazy="joined")
    status_logs = relationship("JobStatusLog", back_populates="job", cascade="all, delete-orphan")
    payments    = relationship("Payment",      back_populates="job", cascade="all, delete-orphan")


class JobStatusLog(Base):
    """Audit log entry recording every status change on a job."""
    __tablename__ = "job_status_logs"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    job_id        = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    prev_status   = Column(String(30))           # None on initial creation
    new_status    = Column(String(30), nullable=False)
    timestamp     = Column(DateTime, default=datetime.now)
    action_source = Column(String(100), default="User")  # Who triggered the change
    job           = relationship("Job", back_populates="status_logs")


class Payment(Base):
    """Stores payment details for a completed or in-progress job."""
    __tablename__ = "payments"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    job_id      = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)
    labor_cost  = Column(Float, default=0.0)
    parts_cost  = Column(Float, default=0.0)
    total_cost  = Column(Float, default=0.0)   # labor_cost + parts_cost
    paid_amount = Column(Float, default=0.0)
    remaining   = Column(Float, default=0.0)   # total_cost - paid_amount
    notes       = Column(Text,  default="")
    paid_at     = Column(DateTime, default=datetime.now)
    job         = relationship("Job", back_populates="payments", lazy="joined")