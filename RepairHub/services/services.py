# Business logic services for the RepairHub application.
# Each service class wraps a SQLAlchemy session and provides
# CRUD operations and domain-specific validation for one entity type.

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, extract

from models.models import (
    Customer, Device, Job, JobStatusLog, Payment,
    VALID_TRANSITIONS,
)
from utils.logger import logger

# Compiled regex patterns used for input validation
_PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_phone(phone: str) -> None:
    """Raise ValueError if the phone number is not 7–20 digits (with optional + prefix)."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if len(cleaned) < 7 or len(cleaned) > 20 or not re.match(r"^\+?\d+$", cleaned):
        raise ValueError("Invalid phone number. Enter digits and + only (7–20 characters).")


def _validate_email(email: str) -> None:
    """Raise ValueError if the email address format is invalid (empty strings are allowed)."""
    if email and not _EMAIL_RE.match(email):
        raise ValueError("Invalid email address.")


def _validate_length(value: str, field_name: str, max_len: int) -> None:
    """Raise ValueError if value is not a string or exceeds the maximum allowed length."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a text value.")
    if len(value) > max_len:
        raise ValueError(f"{field_name} must not exceed {max_len} characters.")


class CustomerService:
    """Provides create, read, update, delete, and search operations for Customer records."""

    def __init__(self, session: Session):
        self.db = session

    def create(self, name: str, phone: str, email: str = "", address: str = "") -> Customer:
        """Create and persist a new customer. Raises ValueError on validation failure or duplicate phone."""
        _validate_phone(phone)
        _validate_email(email)
        _validate_length(name, "Full Name", 100)
        _validate_length(phone, "Phone", 20)
        _validate_length(email, "Email", 100)
        _validate_length(address, "Address", 500)
        if self.db.query(Customer).filter_by(phone=phone).first():
            raise ValueError(f"This phone number is already registered: {phone}")
        c = Customer(name=name, phone=phone, email=email, address=address)
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)
        logger.info(f"Customer created: {name} | {phone}")
        return c

    # Fields that may be updated via the update() method
    _ALLOWED_FIELDS = {"name", "phone", "email", "address"}

    def update(self, cid: int, **kwargs) -> Customer:
        """Update allowed fields of an existing customer record."""
        c = self._get_or_raise(cid)
        unexpected = set(kwargs) - self._ALLOWED_FIELDS
        if unexpected:
            raise ValueError(f"Non-updatable fields: {unexpected}")
        if "phone" in kwargs:
            _validate_phone(kwargs["phone"])
            if kwargs["phone"] != c.phone:
                if self.db.query(Customer).filter_by(phone=kwargs["phone"]).first():
                    raise ValueError(f"This phone number is already registered: {kwargs['phone']}")
        if "email" in kwargs:
            _validate_email(kwargs["email"])
            _validate_length(kwargs["email"], "Email", 100)
        if "name" in kwargs:
            _validate_length(kwargs["name"], "Full Name", 100)
        if "address" in kwargs:
            _validate_length(kwargs["address"], "Address", 500)
        for k, v in kwargs.items():
            setattr(c, k, v)
        self.db.commit()
        self.db.refresh(c)
        logger.info(f"Customer updated: ID={cid}")
        return c

    def delete(self, cid: int) -> None:
        """Delete a customer and all associated devices and jobs (cascade)."""
        c = self._get_or_raise(cid)
        self.db.delete(c)
        self.db.commit()
        logger.info(f"Customer deleted: ID={cid}")

    def get_all(self) -> list[Customer]:
        """Return all customers ordered by creation date descending."""
        return self.db.query(Customer).order_by(Customer.created_at.desc()).all()

    def get_by_id(self, cid: int) -> Optional[Customer]:
        """Return the customer with the given ID, or None if not found."""
        return self.db.get(Customer, cid)

    def search(self, q: str) -> list[Customer]:
        """Search customers by name, phone, or email (case-insensitive partial match)."""
        like = f"%{q}%"
        return self.db.query(Customer).filter(
            or_(Customer.name.ilike(like), Customer.phone.ilike(like), Customer.email.ilike(like))
        ).all()

    def _get_or_raise(self, cid: int) -> Customer:
        """Return the customer or raise ValueError if not found."""
        c = self.db.get(Customer, cid)
        if not c:
            raise ValueError(f"Customer not found: ID={cid}")
        return c


class DeviceService:
    """Provides CRUD operations for Device records."""

    def __init__(self, session: Session):
        self.db = session

    def create(self, customer_id: int, brand: str, model: str, problem_desc: str,
               serial_no: str = "", imei: str = "", image_paths: Optional[list] = None) -> Device:
        """Create and persist a new device for the given customer."""
        if not self.db.get(Customer, customer_id):
            raise ValueError(f"Customer not found: ID={customer_id}")
        _validate_length(brand, "Brand", 60)
        _validate_length(model, "Model", 100)
        _validate_length(serial_no, "Serial No", 100)
        _validate_length(imei, "IMEI", 20)
        _validate_length(problem_desc, "Problem Description", 500)
        d = Device(
            customer_id=customer_id, brand=brand, model=model,
            serial_no=serial_no, imei=imei, problem_desc=problem_desc,
            image_paths=image_paths or [],
        )
        self.db.add(d)
        self.db.commit()
        self.db.refresh(d)
        logger.info(f"Device created: {brand} {model} (Customer ID={customer_id})")
        return d

    # Fields that may be updated via the update() method
    _ALLOWED_FIELDS = {"brand", "model", "serial_no", "imei", "problem_desc", "image_paths"}

    def update(self, did: int, **kwargs) -> Device:
        """Update allowed fields of an existing device record."""
        d = self._get_or_raise(did)
        unexpected = set(kwargs) - self._ALLOWED_FIELDS
        if unexpected:
            raise ValueError(f"Non-updatable fields: {unexpected}")
        if "brand" in kwargs:
            _validate_length(kwargs["brand"], "Brand", 60)
        if "model" in kwargs:
            _validate_length(kwargs["model"], "Model", 100)
        if "serial_no" in kwargs:
            _validate_length(kwargs["serial_no"], "Serial No", 100)
        if "imei" in kwargs:
            _validate_length(kwargs["imei"], "IMEI", 20)
        if "problem_desc" in kwargs:
            _validate_length(kwargs["problem_desc"], "Problem Description", 500)
        for k, v in kwargs.items():
            setattr(d, k, v)
        self.db.commit()
        self.db.refresh(d)
        logger.info(f"Device updated: ID={did}")
        return d

    def delete(self, did: int) -> None:
        """Delete a device and all associated jobs (cascade)."""
        d = self._get_or_raise(did)
        self.db.delete(d)
        self.db.commit()
        logger.info(f"Device deleted: ID={did}")

    def get_all(self) -> list[Device]:
        """Return all devices ordered by entry date descending."""
        return self.db.query(Device).order_by(Device.entry_date.desc()).all()

    def get_by_id(self, did: int) -> Optional[Device]:
        """Return the device with the given ID, or None if not found."""
        return self.db.get(Device, did)

    def get_by_customer(self, customer_id: int) -> list[Device]:
        """Return all devices belonging to the given customer."""
        return self.db.query(Device).filter_by(customer_id=customer_id).all()

    def _get_or_raise(self, did: int) -> Device:
        """Return the device or raise ValueError if not found."""
        d = self.db.get(Device, did)
        if not d:
            raise ValueError(f"Device not found: ID={did}")
        return d


class JobService:
    """Provides CRUD operations and status transition logic for Job (work order) records."""

    def __init__(self, session: Session):
        self.db = session

    def create(self, device_id: int, customer_id: int,
               notes: str = "", technician: str = "") -> Job:
        """Create a new job with initial status 'Received' and log the creation event."""
        if not self.db.get(Customer, customer_id):
            raise ValueError(f"Customer not found: ID={customer_id}")
        if not self.db.get(Device, device_id):
            raise ValueError(f"Device not found: ID={device_id}")
        _validate_length(notes, "Notes", 1000)
        _validate_length(technician, "Technician", 100)
        j = Job(device_id=device_id, customer_id=customer_id,
                status="Received", notes=notes, technician=technician)
        self.db.add(j)
        self.db.flush()
        # Record the initial status in the audit log
        self.db.add(JobStatusLog(job_id=j.id, prev_status=None,
                                 new_status="Received", action_source="System — Job Creation"))
        self.db.commit()
        self.db.refresh(j)
        logger.info(f"Work order created: ID={j.id}")
        return j

    def change_status(self, job_id: int, new_status: str,
                      action_source: str = "User") -> Job:
        """Transition a job to a new status, enforcing VALID_TRANSITIONS rules."""
        j = self._get_or_raise(job_id)
        allowed = VALID_TRANSITIONS.get(j.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {j.status!r} → {new_status!r}. "
                f"Allowed next statuses: {allowed}"
            )
        prev = j.status
        j.status = new_status
        # Append an audit log entry for the transition
        self.db.add(JobStatusLog(job_id=j.id, prev_status=prev,
                                 new_status=new_status, action_source=action_source))
        self.db.commit()
        self.db.refresh(j)
        logger.info(f"Status changed: Job#{job_id} {prev} → {new_status}")
        return j

    def update(self, job_id: int, notes=None, technician=None) -> Job:
        """Update the notes and/or technician fields of an existing job."""
        j = self._get_or_raise(job_id)
        if notes is not None:
            _validate_length(notes, "Notes", 1000)
            j.notes = notes
        if technician is not None:
            _validate_length(technician, "Technician", 100)
            j.technician = technician
        self.db.commit()
        self.db.refresh(j)
        return j

    def delete(self, job_id: int) -> None:
        """Delete a work order and all its status logs and payments (cascade)."""
        j = self._get_or_raise(job_id)
        self.db.delete(j)
        self.db.commit()
        logger.info(f"Work order deleted: ID={job_id}")

    def get_all(self) -> list[Job]:
        """Return all jobs ordered by creation date descending."""
        return self.db.query(Job).order_by(Job.created_at.desc()).all()

    def get_by_id(self, job_id: int) -> Optional[Job]:
        """Return the job with the given ID, or None if not found."""
        return self.db.get(Job, job_id)

    def get_by_customer(self, customer_id: int) -> list[Job]:
        """Return all jobs for the given customer, newest first."""
        return (
            self.db.query(Job)
            .filter_by(customer_id=customer_id)
            .order_by(Job.created_at.desc())
            .all()
        )

    def get_status_log(self, job_id: int) -> list[JobStatusLog]:
        """Return the complete audit log for a job, ordered chronologically."""
        return (
            self.db.query(JobStatusLog)
            .filter_by(job_id=job_id)
            .order_by(JobStatusLog.timestamp)
            .all()
        )

    def search(self, query: str = "", status=None,
               date_from=None, date_to=None) -> list[Job]:
        """Search jobs by customer name/phone, device brand/model/serial, status, and date range."""
        q = (
            self.db.query(Job)
            .join(Customer, Job.customer_id == Customer.id)
            .join(Device,   Job.device_id   == Device.id)
        )
        if query:
            like = f"%{query}%"
            q = q.filter(or_(
                Customer.name.ilike(like), Customer.phone.ilike(like),
                Device.brand.ilike(like),  Device.model.ilike(like),
                Device.serial_no.ilike(like),
            ))
        if status:
            q = q.filter(Job.status == status)
        if date_from:
            q = q.filter(Job.created_at >= date_from)
        if date_to:
            q = q.filter(Job.created_at <= date_to)
        return q.order_by(Job.created_at.desc()).all()

    def _get_or_raise(self, job_id: int) -> Job:
        """Return the job or raise ValueError if not found."""
        j = self.db.get(Job, job_id)
        if not j:
            raise ValueError(f"Work order not found: ID={job_id}")
        return j


class PaymentService:
    """Handles creation, updating, and querying of Payment records."""

    def __init__(self, session: Session):
        self.db = session

    def create_or_update(self, job_id: int, labor_cost: float, parts_cost: float,
                          paid_amount: float = 0.0, notes: str = "") -> Payment:
        """Create a payment record for a job, or update it if one already exists."""
        if not self.db.get(Job, job_id):
            raise ValueError(f"Work order not found: ID={job_id}")
        _validate_length(notes, "Notes", 1000)
        total = labor_cost + parts_cost
        if paid_amount > total:
            raise ValueError(f"Paid amount ({paid_amount:.2f}) cannot exceed total ({total:.2f}).")
        remaining = total - paid_amount
        p = self.db.query(Payment).filter_by(job_id=job_id).first()
        if p:
            # Update existing payment record
            p.labor_cost = labor_cost
            p.parts_cost = parts_cost
            p.total_cost = total
            p.paid_amount = paid_amount
            p.remaining = remaining
            p.notes = notes
            p.paid_at = datetime.now()
        else:
            # Create a new payment record
            p = Payment(job_id=job_id, labor_cost=labor_cost, parts_cost=parts_cost,
                        total_cost=total, paid_amount=paid_amount, remaining=remaining, notes=notes)
            self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        logger.info(f"Payment saved: Job#{job_id} Total={total:.2f} Remaining={remaining:.2f}")
        return p

    def add_partial(self, job_id: int, amount: float) -> Payment:
        """Add a partial payment to an existing payment record."""
        if amount <= 0:
            raise ValueError("Partial payment amount must be positive.")
        p = self.db.query(Payment).filter_by(job_id=job_id).first()
        if not p:
            raise ValueError(f"No payment record found for Job#{job_id}.")
        new_paid = p.paid_amount + amount
        if new_paid > p.total_cost:
            raise ValueError(
                f"Partial payment ({amount:.2f}) would exceed total ({p.total_cost:.2f}). "
                f"Already paid: {p.paid_amount:.2f}"
            )
        p.paid_amount = new_paid
        p.remaining = p.total_cost - new_paid
        p.paid_at = datetime.now()
        self.db.commit()
        self.db.refresh(p)
        logger.info(f"Partial payment added: Job#{job_id} +{amount:.2f} Remaining={p.remaining:.2f}")
        return p

    def get_by_job(self, job_id: int) -> Optional[Payment]:
        """Return the payment record for the given job, or None if not found."""
        return self.db.query(Payment).filter_by(job_id=job_id).first()

    def get_all_with_jobs(self) -> list[Payment]:
        """Return all payment records joined with their associated jobs, newest first."""
        return self.db.query(Payment).join(Job).order_by(Payment.paid_at.desc()).all()

    def monthly_revenue(self, year: int, month: int) -> float:
        """Return the total paid amount across all payments for the given month."""
        result = self.db.query(func.sum(Payment.paid_amount)).filter(
            extract("year",  Payment.paid_at) == year,
            extract("month", Payment.paid_at) == month,
        ).scalar()
        return float(result or 0.0)


class DashboardService:
    """Aggregates statistics for the dashboard overview panel."""

    def __init__(self, session: Session):
        self.db = session

    def get_stats(self) -> dict:
        """Return a dictionary of key metrics: active jobs, revenue, pending payments, etc."""
        now = datetime.now()
        # Statuses that count as active (not finished or cancelled)
        active_statuses = ["Received", "Under Inspection", "In Repair", "Waiting for Parts", "Testing"]
        active_count  = self.db.query(Job).filter(Job.status.in_(active_statuses)).count()
        ready_count   = self.db.query(Job).filter_by(status="Ready").count()
        total_cust    = self.db.query(Customer).count()
        total_devices = self.db.query(Device).count()
        total_jobs    = self.db.query(Job).count()
        monthly_rev   = PaymentService(self.db).monthly_revenue(now.year, now.month)
        pending       = float(self.db.query(func.sum(Payment.remaining)).scalar() or 0.0)
        dist_rows     = self.db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
        status_dist   = {s: c for s, c in dist_rows}
        return {
            "active_jobs":         active_count,
            "ready_jobs":          ready_count,
            "total_customers":     total_cust,
            "total_devices":       total_devices,
            "total_jobs":          total_jobs,
            "monthly_revenue":     monthly_rev,
            "pending_payments":    pending,
            "status_distribution": status_dist,
        }
