"""
Hospital Management System - CRUD Operations Examples
Demonstrates Create, Read, Update, Delete operations for HMS.
"""

from database import DatabaseManager
from models import Patient, Doctor, Appointment, Ward, Admission, Billing, Staff, MedicalRecord
from queries import *
from datetime import datetime, date, timedelta
from typing import List, Optional


class PatientCRUD:
    """CRUD operations for Patient table."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def create(self, patient: Patient) -> int:
        """
        Create new patient.

        Args:
            patient: Patient object with data

        Returns:
            int: newly created patient_id
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                INSERT_PATIENT,
                (patient.name, patient.dob, patient.gender, patient.phone, patient.address, patient.blood_group)
            )
            return cursor.lastrowid

    def read(self, patient_id: int) -> Optional[Patient]:
        """
        Read patient by ID.

        Args:
            patient_id: ID of patient to retrieve

        Returns:
            Patient object or None if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_PATIENT_BY_ID, (patient_id,))
            row = cursor.fetchone()

        if row:
            return Patient(
                patient_id=row['patient_id'],
                name=row['name'],
                dob=row['dob'],
                gender=row['gender'],
                phone=row['phone'],
                address=row['address'],
                blood_group=row['blood_group'],
                created_at=row['created_at']
            )
        return None

    def read_all(self) -> List[Patient]:
        """
        Read all patients.

        Returns:
            List of Patient objects
        """
        patients = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_ALL_PATIENTS)
            rows = cursor.fetchall()

        for row in rows:
            patients.append(Patient(
                patient_id=row['patient_id'],
                name=row['name'],
                dob=row['dob'],
                gender=row['gender'],
                phone=row['phone'],
                address=row['address'],
                blood_group=row['blood_group'],
                created_at=row['created_at']
            ))
        return patients

    def search_by_name(self, name: str) -> List[Patient]:
        """
        Search patients by name.

        Args:
            name: Patient name (partial match allowed)

        Returns:
            List of matching Patient objects
        """
        patients = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SEARCH_PATIENTS_BY_NAME, (f"%{name}%",))
            rows = cursor.fetchall()

        for row in rows:
            patients.append(Patient(
                patient_id=row['patient_id'],
                name=row['name'],
                dob=row['dob'],
                gender=row['gender'],
                phone=row['phone'],
                address=row['address'],
                blood_group=row['blood_group'],
                created_at=row['created_at']
            ))
        return patients

    def update(self, patient: Patient) -> bool:
        """
        Update patient information.

        Args:
            patient: Patient object with updated data

        Returns:
            bool: True if successful
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                UPDATE_PATIENT,
                (patient.name, patient.dob, patient.gender, patient.phone, patient.address, patient.blood_group, patient.patient_id)
            )
            return cursor.rowcount > 0

    def delete(self, patient_id: int) -> bool:
        """
        Delete patient record.

        Args:
            patient_id: ID of patient to delete

        Returns:
            bool: True if successful
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(DELETE_PATIENT, (patient_id,))
            return cursor.rowcount > 0


class AppointmentCRUD:
    """CRUD operations for Appointment table."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def create(self, appointment: Appointment) -> int:
        """
        Create new appointment.

        Args:
            appointment: Appointment object with data

        Returns:
            int: newly created appointment_id
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                INSERT_APPOINTMENT,
                (appointment.patient_id, appointment.doctor_id, appointment.appointment_date,
                 appointment.time_slot, appointment.status, appointment.notes)
            )
            return cursor.lastrowid

    def read(self, appointment_id: int) -> Optional[Appointment]:
        """
        Read appointment by ID.

        Args:
            appointment_id: ID of appointment to retrieve

        Returns:
            Appointment object or None if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))
            row = cursor.fetchone()

        if row:
            return Appointment(
                appointment_id=row['appointment_id'],
                patient_id=row['patient_id'],
                doctor_id=row['doctor_id'],
                appointment_date=row['appointment_date'],
                time_slot=row['time_slot'],
                status=row['status'],
                notes=row['notes'],
                created_at=row['created_at']
            )
        return None

    def get_by_patient(self, patient_id: int) -> List[Appointment]:
        """
        Get all appointments for a patient.

        Args:
            patient_id: ID of patient

        Returns:
            List of Appointment objects
        """
        appointments = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_APPOINTMENTS_BY_PATIENT, (patient_id,))
            rows = cursor.fetchall()

        for row in rows:
            appointments.append(Appointment(
                appointment_id=row['appointment_id'],
                patient_id=row['patient_id'],
                doctor_id=row['doctor_id'],
                appointment_date=row['appointment_date'],
                time_slot=row['time_slot'],
                status=row['status'],
                notes=row['notes'],
                created_at=row['created_at']
            ))
        return appointments

    def get_by_doctor(self, doctor_id: int) -> List[Appointment]:
        """
        Get all appointments for a doctor.

        Args:
            doctor_id: ID of doctor

        Returns:
            List of Appointment objects
        """
        appointments = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_APPOINTMENTS_BY_DOCTOR, (doctor_id,))
            rows = cursor.fetchall()

        for row in rows:
            appointments.append(Appointment(
                appointment_id=row['appointment_id'],
                patient_id=row['patient_id'],
                doctor_id=row['doctor_id'],
                appointment_date=row['appointment_date'],
                time_slot=row['time_slot'],
                status=row['status'],
                notes=row['notes'],
                created_at=row['created_at']
            ))
        return appointments

    def get_today_appointments(self) -> List[dict]:
        """
        Get all appointments scheduled for today.

        Returns:
            List of appointment records with patient and doctor names
        """
        appointments = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_APPOINTMENTS_TODAY)
            rows = cursor.fetchall()

        for row in rows:
            appointments.append({
                'appointment_id': row['appointment_id'],
                'patient_name': row['patient_name'],
                'doctor_name': row['doctor_name'],
                'time_slot': row['time_slot'],
                'status': row['status'],
                'notes': row['notes']
            })
        return appointments

    def update_status(self, appointment_id: int, status: str) -> bool:
        """
        Update appointment status.

        Args:
            appointment_id: ID of appointment
            status: New status (scheduled, completed, cancelled)

        Returns:
            bool: True if successful
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(UPDATE_APPOINTMENT_STATUS, (status, appointment_id))
            return cursor.rowcount > 0

    def cancel(self, appointment_id: int) -> bool:
        """
        Cancel appointment.

        Args:
            appointment_id: ID of appointment to cancel

        Returns:
            bool: True if successful
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CANCEL_APPOINTMENT, (appointment_id,))
            return cursor.rowcount > 0


class BillingCRUD:
    """CRUD operations for Billing table."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def create(self, billing: Billing) -> int:
        """
        Create new bill.

        Args:
            billing: Billing object with data

        Returns:
            int: newly created bill_id
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                INSERT_BILL,
                (billing.patient_id, billing.admission_id, billing.total_amount, 
                 billing.paid_amount, billing.payment_status)
            )
            return cursor.lastrowid

    def get_by_patient(self, patient_id: int) -> List[Billing]:
        """
        Get all bills for a patient.

        Args:
            patient_id: ID of patient

        Returns:
            List of Billing objects
        """
        bills = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_BILLS_BY_PATIENT, (patient_id,))
            rows = cursor.fetchall()

        for row in rows:
            bills.append(Billing(
                bill_id=row['bill_id'],
                patient_id=row['patient_id'],
                admission_id=row['admission_id'],
                total_amount=row['total_amount'],
                paid_amount=row['paid_amount'],
                payment_status=row['payment_status'],
                payment_date=row['payment_date'],
                created_at=row['created_at']
            ))
        return bills

    def get_pending_bills(self) -> List[dict]:
        """
        Get all pending and partial payment bills.

        Returns:
            List of pending bill records with patient names
        """
        bills = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_PENDING_BILLS)
            rows = cursor.fetchall()

        for row in rows:
            bills.append({
                'bill_id': row['bill_id'],
                'patient_name': row['patient_name'],
                'total_amount': row['total_amount'],
                'paid_amount': row['paid_amount'],
                'outstanding': row['total_amount'] - row['paid_amount'],
                'payment_status': row['payment_status']
            })
        return bills

    def record_payment(self, bill_id: int, amount_paid: float) -> bool:
        """
        Record payment for a bill.

        Args:
            bill_id: ID of bill
            amount_paid: Amount paid

        Returns:
            bool: True if successful
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get current bill info
            cursor.execute("SELECT total_amount, paid_amount FROM billing WHERE bill_id = ?", (bill_id,))
            row = cursor.fetchone()

            if not row:
                return False

            new_paid_amount = row['paid_amount'] + amount_paid
            total_amount = row['total_amount']

            # Determine payment status
            if new_paid_amount >= total_amount:
                payment_status = 'paid'
            elif new_paid_amount > 0:
                payment_status = 'partial'
            else:
                payment_status = 'pending'

            cursor.execute(
                UPDATE_BILL_PAYMENT,
                (new_paid_amount, payment_status, datetime.now(), bill_id)
            )
            return cursor.rowcount > 0


# Example usage
if __name__ == "__main__":
    # Initialize database
    db_manager = DatabaseManager("hms_database.db")

    # Example: Create a new patient
    print("=== PATIENT CRUD EXAMPLES ===\n")
    patient_crud = PatientCRUD(db_manager)

    # Create
    new_patient = Patient(
        name="John Doe",
        dob=date(1980, 5, 15),
        gender="M",
        phone="9999888877",
        address="100 Health St, City",
        blood_group="A+"
    )
    patient_id = patient_crud.create(new_patient)
    print(f"✓ Created patient with ID: {patient_id}")

    # Read
    patient = patient_crud.read(patient_id)
    print(f"✓ Retrieved patient: {patient}")

    # Search
    results = patient_crud.search_by_name("John")
    print(f"✓ Search results for 'John': {len(results)} found")

    # Update
    patient.phone = "9999888888"
    patient_crud.update(patient)
    print(f"✓ Updated patient phone")

    # Example: Appointment operations
    print("\n=== APPOINTMENT CRUD EXAMPLES ===\n")
    appointment_crud = AppointmentCRUD(db_manager)

    # Get today's appointments
    today_appts = appointment_crud.get_today_appointments()
    print(f"✓ Today's appointments: {len(today_appts)}")
    for appt in today_appts[:3]:
        print(f"  - {appt['patient_name']} with {appt['doctor_name']} at {appt['time_slot']}")

    # Create new appointment
    new_appt = Appointment(
        patient_id=patient_id,
        doctor_id=1,
        appointment_date=date.today() + timedelta(days=3),
        time_slot="02:00 PM",
        status="scheduled",
        notes="General checkup"
    )
    appt_id = appointment_crud.create(new_appt)
    print(f"\n✓ Created appointment with ID: {appt_id}")

    # Example: Billing operations
    print("\n=== BILLING CRUD EXAMPLES ===\n")
    billing_crud = BillingCRUD(db_manager)

    # Get pending bills
    pending = billing_crud.get_pending_bills()
    print(f"✓ Pending bills: {len(pending)}")
    for bill in pending[:3]:
        print(f"  - {bill['patient_name']}: Rs. {bill['outstanding']} outstanding")

    print("\n✓ CRUD operations completed successfully")
