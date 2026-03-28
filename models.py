"""
Hospital Management System - Data Models
Dataclasses representing database entities for HMS.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class Patient:
    """Patient entity model."""
    patient_id: Optional[int] = None
    name: str = ""
    dob: date = None
    gender: str = ""  # M, F, Other
    phone: str = ""
    address: str = ""
    blood_group: str = ""
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"Patient(id={self.patient_id}, name={self.name}, phone={self.phone})"


@dataclass
class Doctor:
    """Doctor entity model."""
    doctor_id: Optional[int] = None
    name: str = ""
    specialization: str = ""
    phone: str = ""
    email: str = ""
    available_days: str = "Mon-Fri"
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"Doctor(id={self.doctor_id}, name={self.name}, spec={self.specialization})"


@dataclass
class Appointment:
    """Appointment entity model."""
    appointment_id: Optional[int] = None
    patient_id: int = 0
    doctor_id: int = 0
    appointment_date: date = None
    time_slot: str = ""
    status: str = "scheduled"  # scheduled, completed, cancelled
    notes: str = ""
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"Appointment(id={self.appointment_id}, date={self.appointment_date}, status={self.status})"


@dataclass
class Ward:
    """Ward entity model."""
    ward_id: Optional[int] = None
    ward_name: str = ""
    ward_type: str = ""  # general, ICU, private
    total_beds: int = 0
    available_beds: int = 0

    def __repr__(self) -> str:
        return f"Ward(id={self.ward_id}, name={self.ward_name}, available={self.available_beds}/{self.total_beds})"


@dataclass
class Admission:
    """Admission entity model."""
    admission_id: Optional[int] = None
    patient_id: int = 0
    ward_id: int = 0
    doctor_id: int = 0
    admission_date: datetime = None
    discharge_date: Optional[datetime] = None
    diagnosis: str = ""
    status: str = "admitted"  # admitted, discharged, transferred

    def __repr__(self) -> str:
        return f"Admission(id={self.admission_id}, patient_id={self.patient_id}, status={self.status})"


@dataclass
class Billing:
    """Billing entity model."""
    bill_id: Optional[int] = None
    patient_id: int = 0
    admission_id: Optional[int] = None
    total_amount: float = 0.0
    paid_amount: float = 0.0
    payment_status: str = "pending"  # pending, partial, paid
    payment_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @property
    def outstanding_amount(self) -> float:
        """Calculate outstanding amount."""
        return self.total_amount - self.paid_amount

    def __repr__(self) -> str:
        return f"Billing(bill_id={self.bill_id}, patient_id={self.patient_id}, status={self.payment_status})"


@dataclass
class Staff:
    """Staff entity model."""
    staff_id: Optional[int] = None
    name: str = ""
    role: str = ""
    department: str = ""
    phone: str = ""
    shift: str = ""  # morning, evening, night
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"Staff(id={self.staff_id}, name={self.name}, role={self.role})"


@dataclass
class MedicalRecord:
    """Medical record entity model."""
    record_id: Optional[int] = None
    patient_id: int = 0
    doctor_id: int = 0
    visit_date: datetime = None
    diagnosis: str = ""
    prescription: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"MedicalRecord(id={self.record_id}, patient_id={self.patient_id}, date={self.visit_date})"
