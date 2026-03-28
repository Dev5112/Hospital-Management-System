"""
Hospital Management System - Example & Testing
Demonstrates comprehensive usage of HMS database system.
"""

from database import DatabaseManager
from models import Patient, Doctor, Appointment, Billing
from crud_operations import PatientCRUD, AppointmentCRUD, BillingCRUD
from queries import *
from datetime import datetime, date, timedelta


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_patient_operations(db_manager: DatabaseManager):
    """Demonstrate patient CRUD operations."""
    print_section("PATIENT OPERATIONS")

    patient_crud = PatientCRUD(db_manager)

    # Get all patients
    print("1. Fetching all patients:")
    print("-" * 70)
    patients = patient_crud.read_all()
    for patient in patients[:3]:
        print(f"   {patient.patient_id:3} | {patient.name:20} | {patient.phone:12} | {patient.blood_group}")
    print(f"   ... ({len(patients)} total patients)\n")

    # Search patients
    print("2. Searching for patients by name:")
    print("-" * 70)
    search_results = patient_crud.search_by_name("Raj")
    for patient in search_results:
        print(f"   {patient.patient_id:3} | {patient.name:20} | Age: {calculate_age(patient.dob)}")
    print()

    # Get single patient details
    print("3. Patient details (ID: 1):")
    print("-" * 70)
    patient = patient_crud.read(1)
    if patient:
        print(f"   Name:        {patient.name}")
        print(f"   DOB:         {patient.dob}")
        print(f"   Gender:      {patient.gender}")
        print(f"   Phone:       {patient.phone}")
        print(f"   Blood Group: {patient.blood_group}")
        print(f"   Address:     {patient.address}")
        print(f"   Created:     {patient.created_at}\n")


def demo_appointment_operations(db_manager: DatabaseManager):
    """Demonstrate appointment CRUD operations."""
    print_section("APPOINTMENT OPERATIONS")

    appointment_crud = AppointmentCRUD(db_manager)

    # Get today's appointments
    print("1. Today's appointments:")
    print("-" * 70)
    today_appts = appointment_crud.get_today_appointments()
    if today_appts:
        for appt in today_appts:
            print(f"   {appt['time_slot']:10} | {appt['patient_name']:20} | Dr. {appt['doctor_name']:20} | {appt['status']}")
    else:
        print("   No appointments scheduled for today\n")

    # Get patient appointments
    print("\n2. Appointments for Patient ID 2:")
    print("-" * 70)
    patient_appts = appointment_crud.get_by_patient(2)
    for appt in patient_appts:
        print(f"   {appt.appointment_date} | {appt.time_slot:10} | Status: {appt.status}")
    print()

    # Get doctor appointments
    print("3. Appointments for Doctor ID 1:")
    print("-" * 70)
    doctor_appts = appointment_crud.get_by_doctor(1)
    print(f"   Total appointments: {len(doctor_appts)}\n")


def demo_billing_operations(db_manager: DatabaseManager):
    """Demonstrate billing operations."""
    print_section("BILLING OPERATIONS")

    billing_crud = BillingCRUD(db_manager)

    # Get pending bills
    print("1. Pending and partial payment bills:")
    print("-" * 70)
    pending_bills = billing_crud.get_pending_bills()
    if pending_bills:
        print(f"   {'Patient':<20} {'Total':<12} {'Paid':<12} {'Outstanding':<12} {'Status':<10}")
        print("   " + "-" * 66)
        for bill in pending_bills:
            print(f"   {bill['patient_name']:<20} Rs. {bill['total_amount']:<11.2f} Rs. {bill['paid_amount']:<11.2f} Rs. {bill['outstanding']:<11.2f} {bill['payment_status']:<10}")
    print()


def demo_analytics(db_manager: DatabaseManager):
    """Demonstrate analytics and reporting."""
    print_section("ANALYTICS & REPORTING")

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()

        # Ward occupancy
        print("1. Ward Occupancy Status:")
        print("-" * 70)
        cursor.execute(GET_WARD_OCCUPANCY)
        rows = cursor.fetchall()
        for row in rows:
            print(f"   {row['ward_name']:<20} | Beds: {row['occupied_beds']:2}/{row['total_beds']:2} | Occupancy: {row['occupancy_rate']:6.2f}%")
        print()

        # Revenue summary
        print("2. Revenue Summary:")
        print("-" * 70)
        cursor.execute(GET_REVENUE_SUMMARY)
        rows = cursor.fetchall()
        total_revenue = 0
        for row in rows:
            print(f"   {row['payment_status'].upper():10} | Bills: {row['bill_count']:3} | Amount: Rs. {row['total_amount']:.2f}")
            total_revenue += row['total_amount'] if row['total_amount'] else 0
        print(f"   {'-' * 66}")
        print(f"   {'TOTAL':<10} | {'':4} | Amount: Rs. {total_revenue:.2f}\n")

        # Doctor performance
        print("3. Doctor Performance Metrics:")
        print("-" * 70)
        cursor.execute(GET_DOCTOR_PERFORMANCE)
        rows = cursor.fetchall()
        for row in rows:
            completion_rate = (row['completed_appointments'] / row['total_appointments'] * 100) if row['total_appointments'] > 0 else 0
            print(f"   Dr. {row['name']:<20} ({row['specialization']:<15}) | Completed: {completion_rate:6.2f}%")
        print()


def demo_database_stats(db_manager: DatabaseManager):
    """Display database statistics."""
    print_section("DATABASE STATISTICS")

    stats = db_manager.get_db_stats()

    print("Current Database State:")
    print("-" * 70)
    print(f"   Total Patients:         {stats['patients']:5}")
    print(f"   Total Doctors:          {stats['doctors']:5}")
    print(f"   Total Appointments:     {stats['appointments']:5}")
    print(f"   Currently Admitted:     {stats['active_admissions']:5}")
    print(f"   Available Beds:         {stats['available_beds']:5}")
    print(f"   Pending Bills:          {stats['pending_bills']:5}\n")


def calculate_age(dob):
    """Calculate age from date of birth."""
    if isinstance(dob, str):
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def main():
    """Run comprehensive HMS demonstration."""
    print("\n" + "=" * 70)
    print(" " * 15 + "HOSPITAL MANAGEMENT SYSTEM DEMO")
    print("=" * 70)

    # Initialize database
    db_manager = DatabaseManager("hms_demo.db")

    # Create tables and seed data
    print("\nInitializing database...")
    db_manager.create_tables()
    db_manager.seed_data()

    # Display statistics
    demo_database_stats(db_manager)

    # Run demonstrations
    demo_patient_operations(db_manager)
    demo_appointment_operations(db_manager)
    demo_billing_operations(db_manager)
    demo_analytics(db_manager)

    print("=" * 70)
    print("  Demo completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
