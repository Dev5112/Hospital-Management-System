"""
Hospital Management System - CRUD Operations
Example CRUD (Create, Read, Update, Delete) operations for HMS entities.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from database import DatabaseManager
from models import Patient, Appointment, Billing
import queries


class PatientCRUD:
    """CRUD operations for Patient entity."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def create(self, patient: Patient) -> int:
        """
        Create a new patient.

        Args:
            patient: Patient object to create

        Returns:
            ID of the newly created patient
        """
        _, patient_id = self.db.execute_write_query(
            queries.INSERT_PATIENT,
            (patient.name, patient.dob, patient.gender, patient.phone,
             patient.address, patient.blood_group)
        )
        return patient_id

    def read(self, patient_id: int) -> Optional[dict]:
        """
        Retrieve a patient by ID.

        Args:
            patient_id: ID of the patient

        Returns:
            Dictionary with patient data or None if not found
        """
        results = self.db.execute_query(
            queries.SELECT_PATIENT_BY_ID,
            (patient_id,)
        )
        if results:
            return dict(results[0])
        return None

    def read_by_phone(self, phone: str) -> Optional[dict]:
        """
        Retrieve a patient by phone number.

        Args:
            phone: Patient phone number

        Returns:
            Dictionary with patient data or None if not found
        """
        results = self.db.execute_query(
            queries.SELECT_PATIENT_BY_PHONE,
            (phone,)
        )
        if results:
            return dict(results[0])
        return None

    def read_all(self) -> List[dict]:
        """
        Retrieve all patients.

        Returns:
            List of patient dictionaries
        """
        results = self.db.execute_query(queries.SELECT_ALL_PATIENTS)
        return [dict(row) for row in results]

    def search_by_name(self, name: str) -> List[dict]:
        """
        Search patients by name (partial match).

        Args:
            name: Name or partial name to search

        Returns:
            List of matching patient dictionaries
        """
        results = self.db.execute_query(
            queries.SEARCH_PATIENTS_BY_NAME,
            (f"%{name}%",)
        )
        return [dict(row) for row in results]

    def search_by_blood_group(self, blood_group: str) -> List[dict]:
        """
        Search patients by blood group.

        Args:
            blood_group: Blood group to search

        Returns:
            List of patient dictionaries with matching blood group
        """
        results = self.db.execute_query(
            queries.SEARCH_PATIENTS_BY_BLOOD_GROUP,
            (blood_group,)
        )
        return [dict(row) for row in results]

    def update(self, patient: Patient) -> int:
        """
        Update an existing patient.

        Args:
            patient: Patient object with updated data (must have patient_id set)

        Returns:
            Number of rows affected
        """
        return self.db.execute_write_query(
            queries.UPDATE_PATIENT,
            (patient.name, patient.dob, patient.gender, patient.phone,
             patient.address, patient.blood_group, patient.patient_id)
        )

    def delete(self, patient_id: int) -> int:
        """
        Delete a patient by ID.

        Args:
            patient_id: ID of the patient to delete

        Returns:
            Number of rows affected
        """
        return self.db.execute_write_query(
            queries.DELETE_PATIENT,
            (patient_id,)
        )

    def count(self) -> int:
        """
        Get total number of patients.

        Returns:
            Total patient count
        """
        results = self.db.execute_query(queries.COUNT_PATIENTS)
        return results[0][0] if results else 0


class AppointmentCRUD:
    """CRUD operations for Appointment entity."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def create(self, appointment: Appointment) -> int:
        """
        Create a new appointment.

        Args:
            appointment: Appointment object to create

        Returns:
            ID of the newly created appointment
        """
        _, apt_id = self.db.execute_write_query(
            queries.INSERT_APPOINTMENT,
            (appointment.patient_id, appointment.doctor_id,
             appointment.appointment_date, appointment.time_slot,
             appointment.status, appointment.notes)
        )
        return apt_id

    def read_by_patient(self, patient_id: int) -> List[dict]:
        """
        Get all appointments for a patient.

        Args:
            patient_id: ID of the patient

        Returns:
            List of appointment dictionaries
        """
        results = self.db.execute_query(
            queries.SELECT_APPOINTMENTS_BY_PATIENT,
            (patient_id,)
        )
        return [dict(row) for row in results]

    def read_by_doctor(self, doctor_id: int) -> List[dict]:
        """
        Get all appointments for a doctor.

        Args:
            doctor_id: ID of the doctor

        Returns:
            List of appointment dictionaries
        """
        results = self.db.execute_query(
            queries.SELECT_APPOINTMENTS_BY_DOCTOR,
            (doctor_id,)
        )
        return [dict(row) for row in results]

    def read_by_date(self, appointment_date: date) -> List[dict]:
        """
        Get all appointments for a specific date.

        Args:
            appointment_date: Date to query

        Returns:
            List of appointment dictionaries
        """
        results = self.db.execute_query(
            queries.SELECT_APPOINTMENTS_BY_DATE,
            (appointment_date,)
        )
        return [dict(row) for row in results]

    def read_upcoming(self) -> List[dict]:
        """
        Get all upcoming scheduled appointments.

        Returns:
            List of upcoming appointment dictionaries
        """
        results = self.db.execute_query(queries.SELECT_UPCOMING_APPOINTMENTS)
        return [dict(row) for row in results]

    def read_all(self) -> List[dict]:
        """
        Get all appointments.

        Returns:
            List of all appointment dictionaries
        """
        results = self.db.execute_query(queries.SELECT_ALL_APPOINTMENTS)
        return [dict(row) for row in results]

    def update_status(self, appointment_id: int, status: str, notes: Optional[str] = None) -> int:
        """
        Update appointment status and notes.

        Args:
            appointment_id: ID of the appointment
            status: New status (Scheduled/Completed/Cancelled)
            notes: Optional notes to update

        Returns:
            Number of rows affected
        """
        return self.db.execute_write_query(
            queries.UPDATE_APPOINTMENT,
            (status, notes, appointment_id)
        )

    def cancel(self, appointment_id: int) -> int:
        """
        Cancel an appointment.

        Args:
            appointment_id: ID of the appointment to cancel

        Returns:
            Number of rows affected
        """
        return self.db.execute_write_query(
            queries.CANCEL_APPOINTMENT,
            (appointment_id,)
        )

    def delete(self, appointment_id: int) -> int:
        """
        Delete an appointment.

        Args:
            appointment_id: ID of the appointment to delete

        Returns:
            Number of rows affected
        """
        return self.db.execute_write_query(
            queries.DELETE_APPOINTMENT,
            (appointment_id,)
        )


class BillingCRUD:
    """CRUD operations for Billing entity."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def create(self, billing: Billing) -> int:
        """
        Create a new billing record.

        Args:
            billing: Billing object to create

        Returns:
            ID of the newly created bill
        """
        _, bill_id = self.db.execute_write_query(
            queries.INSERT_BILL,
            (billing.patient_id, billing.admission_id,
             billing.total_amount, billing.paid_amount,
             billing.payment_status, billing.payment_date)
        )
        return bill_id

    def read_by_patient(self, patient_id: int) -> List[dict]:
        """
        Get all bills for a patient.

        Args:
            patient_id: ID of the patient

        Returns:
            List of billing dictionaries
        """
        results = self.db.execute_query(
            queries.SELECT_BILLS_BY_PATIENT,
            (patient_id,)
        )
        return [dict(row) for row in results]

    def read_unpaid(self) -> List[dict]:
        """
        Get all unpaid and partially paid bills.

        Returns:
            List of unpaid billing dictionaries
        """
        results = self.db.execute_query(queries.SELECT_UNPAID_BILLS)
        return [dict(row) for row in results]

    def read_all(self) -> List[dict]:
        """
        Get all billing records.

        Returns:
            List of all billing dictionaries
        """
        results = self.db.execute_query(queries.SELECT_ALL_BILLS)
        return [dict(row) for row in results]

    def record_payment(self, bill_id: int, payment_amount: float) -> int:
        """
        Record a payment for a bill.

        Args:
            bill_id: ID of the bill
            payment_amount: Amount paid

        Returns:
            Number of rows affected
        """
        # Get the bill first
        results = self.db.execute_query(
            queries.SELECT_BILL_BY_ID,
            (bill_id,)
        )
        if not results:
            return 0

        bill = dict(results[0])
        new_paid = bill['paid_amount'] + payment_amount
        total = bill['total_amount']

        # Determine new status
        if new_paid >= total:
            status = "Paid"
            new_paid = total
        else:
            status = "Partial"

        return self.db.execute_write_query(
            queries.UPDATE_BILL_PAYMENT,
            (new_paid, status, datetime.now(), bill_id)
        )

    def get_total_revenue(self) -> float:
        """
        Calculate total revenue (paid amounts).

        Returns:
            Total revenue amount
        """
        results = self.db.execute_query(queries.CALCULATE_TOTAL_REVENUE)
        return results[0][0] if results and results[0][0] else 0.0

    def get_pending_amount(self) -> float:
        """
        Calculate total pending payments.

        Returns:
            Total pending amount
        """
        results = self.db.execute_query(queries.CALCULATE_PENDING_PAYMENTS)
        return results[0][0] if results and results[0][0] else 0.0


# ==================== EXAMPLE USAGE ====================

def demo_crud_operations():
    """Demonstrate CRUD operations."""
    db = DatabaseManager()

    # Initialize database if needed
    try:
        db.create_tables()
        db.seed_data()
    except Exception:
        pass  # Tables may already exist

    # ============= Patient CRUD Examples =============
    print("\n" + "="*60)
    print("PATIENT CRUD OPERATIONS")
    print("="*60)

    patient_crud = PatientCRUD(db)

    # Create a new patient
    new_patient = Patient(
        name="Alice Brown",
        dob=date(1992, 6, 15),
        gender="Female",
        phone="9877777777",
        address="999 New St, City",
        blood_group="O+"
    )
    patient_id = patient_crud.create(new_patient)
    print(f"\n✓ Created patient with ID: {patient_id}")

    # Read a patient
    patient_data = patient_crud.read(patient_id)
    print(f"✓ Retrieved patient: {patient_data['name']}")

    # Read all patients
    all_patients = patient_crud.read_all()
    print(f"✓ Total patients: {patient_crud.count()}")

    # Search patients by name
    search_results = patient_crud.search_by_name("John")
    print(f"✓ Found {len(search_results)} patient(s) with 'John' in name")

    # Search by blood group
    blood_group_results = patient_crud.search_by_blood_group("O+")
    print(f"✓ Found {len(blood_group_results)} patient(s) with blood group O+")

    # Update patient
    if patient_data:
        new_patient.patient_id = patient_id
        new_patient.address = "Updated address, New City"
        patient_crud.update(new_patient)
        print(f"✓ Updated patient address")

    # ============= Appointment CRUD Examples =============
    print("\n" + "="*60)
    print("APPOINTMENT CRUD OPERATIONS")
    print("="*60)

    appointment_crud = AppointmentCRUD(db)

    # Create a new appointment
    new_appointment = Appointment(
        patient_id=1,
        doctor_id=1,
        appointment_date=date.today() + timedelta(days=3),
        time_slot="04:00 PM",
        status="Scheduled",
        notes="Follow-up consultation"
    )
    apt_id = appointment_crud.create(new_appointment)
    print(f"\n✓ Created appointment with ID: {apt_id}")

    # Read appointments for a patient
    patient_apts = appointment_crud.read_by_patient(1)
    print(f"✓ Patient 1 has {len(patient_apts)} appointment(s)")

    # Read appointments for a doctor
    doctor_apts = appointment_crud.read_by_doctor(1)
    print(f"✓ Doctor 1 has {len(doctor_apts)} appointment(s)")

    # Get upcoming appointments
    upcoming = appointment_crud.read_upcoming()
    print(f"✓ Total upcoming appointments: {len(upcoming)}")

    # Update appointment status
    appointment_crud.update_status(apt_id, "Completed", "Consultation completed successfully")
    print(f"✓ Updated appointment status to Completed")

    # ============= Billing CRUD Examples =============
    print("\n" + "="*60)
    print("BILLING CRUD OPERATIONS")
    print("="*60)

    billing_crud = BillingCRUD(db)

    # Create a new bill
    new_bill = Billing(
        patient_id=1,
        admission_id=1,
        total_amount=50000.0,
        paid_amount=0.0,
        payment_status="Pending"
    )
    bill_id = billing_crud.create(new_bill)
    print(f"\n✓ Created bill with ID: {bill_id}")

    # Read bills for a patient
    patient_bills = billing_crud.read_by_patient(1)
    print(f"✓ Patient 1 has {len(patient_bills)} bill(s)")

    # Get unpaid bills
    unpaid_bills = billing_crud.read_unpaid()
    print(f"✓ Total unpaid bills: {len(unpaid_bills)}")

    # Record a payment
    billing_crud.record_payment(bill_id, 25000.0)
    print(f"✓ Recorded partial payment of 25000")

    # Get financial summary
    total_revenue = billing_crud.get_total_revenue()
    pending_amount = billing_crud.get_pending_amount()
    print(f"✓ Total revenue: ₹{total_revenue}")
    print(f"✓ Pending amount: ₹{pending_amount}")

    print("\n" + "="*60)
    print("✓ ALL CRUD OPERATIONS COMPLETED SUCCESSFULLY!")
    print("="*60)


if __name__ == "__main__":
    demo_crud_operations()
