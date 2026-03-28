"""
Hospital Management System - Main Application
Entry point for the HMS application demonstrating database initialization and usage.
"""

from database import initialize_database, DatabaseManager
from crud import PatientCRUD, AppointmentCRUD, BillingCRUD
from models import Patient, Appointment, Billing
from datetime import date, datetime, timedelta
import queries


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def display_patients_summary() -> None:
    """Display summary of all patients."""
    db = DatabaseManager()
    patient_crud = PatientCRUD(db)

    print_header("PATIENTS SUMMARY")
    all_patients = patient_crud.read_all()

    if not all_patients:
        print("No patients found.")
        return

    print(f"{'ID':<5} {'Name':<20} {'Phone':<12} {'Blood Group':<12} {'Status':<15}")
    print("-" * 70)

    for patient in all_patients[:10]:  # Show first 10
        print(f"{patient['patient_id']:<5} {patient['name']:<20} {patient['phone']:<12} "
              f"{patient['blood_group'] or 'N/A':<12} {'Active':<15}")

    print(f"\nTotal Patients: {patient_crud.count()}")


def display_appointments_summary() -> None:
    """Display upcoming appointments."""
    db = DatabaseManager()
    apt_crud = AppointmentCRUD(db)

    print_header("UPCOMING APPOINTMENTS")
    upcoming = apt_crud.read_upcoming()

    if not upcoming:
        print("No upcoming appointments.")
        return

    print(f"{'Date':<12} {'Time':<12} {'Patient':<20} {'Doctor':<20}")
    print("-" * 70)

    for apt in upcoming[:10]:  # Show first 10
        print(f"{apt['appointment_date']:<12} {apt['time_slot']:<12} "
              f"{apt['patient_name']:<20} {apt['doctor_name']:<20}")

    print(f"\nTotal Upcoming: {len(upcoming)}")


def display_billing_summary() -> None:
    """Display billing and revenue information."""
    db = DatabaseManager()
    billing_crud = BillingCRUD(db)

    print_header("BILLING & REVENUE SUMMARY")

    total_revenue = billing_crud.get_total_revenue()
    pending_amount = billing_crud.get_pending_amount()
    unpaid_bills = billing_crud.read_unpaid()

    print(f"Total Revenue Collected:    ₹{total_revenue:,.2f}")
    print(f"Total Pending Payments:     ₹{pending_amount:,.2f}")
    print(f"Outstanding Bills Count:    {len(unpaid_bills)}")

    if unpaid_bills:
        print("\nTop 5 Unpaid Bills:")
        print(f"{'Bill ID':<8} {'Patient':<20} {'Amount':<12} {'Status':<12}")
        print("-" * 70)

        for bill in unpaid_bills[:5]:
            print(f"{bill['bill_id']:<8} {bill['patient_name']:<20} "
                  f"₹{bill['total_amount']:<11,.0f} {bill['payment_status']:<12}")


def display_ward_occupancy() -> None:
    """Display ward occupancy information."""
    db = DatabaseManager()

    print_header("WARD OCCUPANCY STATUS")

    results = db.execute_query(queries.WARD_OCCUPANCY)

    if not results:
        print("No ward data available.")
        return

    print(f"{'Ward':<20} {'Total':<8} {'Occupied':<10} {'Occupancy':<12}")
    print("-" * 70)

    for ward in results:
        ward_dict = dict(ward)
        print(f"{ward_dict['ward_name']:<20} {ward_dict['total_beds']:<8} "
              f"{ward_dict['occupied_beds']:<10} {ward_dict['occupancy_percentage']:.1f}%")


def display_statistics() -> None:
    """Display overall HMS statistics."""
    db = DatabaseManager()

    print_header("HOSPITAL MANAGEMENT SYSTEM - STATISTICS")

    results = db.execute_query(queries.STATISTICS_SUMMARY)

    if not results:
        print("No data available.")
        return

    stats = dict(results[0])

    print(f"Total Patients:              {stats['total_patients']}")
    print(f"Total Doctors:               {stats['total_doctors']}")
    print(f"Active Admissions:           {stats['active_admissions']}")
    print(f"Upcoming Appointments:       {stats['upcoming_appointments']}")
    print(f"Total Staff Members:         {stats['total_staff']}")
    print(f"Total Billing Amount:        ₹{stats['total_billing_amount'] or 0:,.0f}")


def demo_create_appointment() -> None:
    """Create a sample appointment."""
    db = DatabaseManager()
    apt_crud = AppointmentCRUD(db)

    print_header("CREATE NEW APPOINTMENT - DEMO")

    # Create appointment
    new_apt = Appointment(
        patient_id=2,
        doctor_id=3,
        appointment_date=date.today() + timedelta(days=5),
        time_slot="10:00 AM",
        status="Scheduled",
        notes="Routine pediatric checkup"
    )

    apt_id = apt_crud.create(new_apt)
    print(f"✓ Appointment created successfully!")
    print(f"  Appointment ID: {apt_id}")
    print(f"  Patient ID: {new_apt.patient_id}")
    print(f"  Doctor ID: {new_apt.doctor_id}")
    print(f"  Date: {new_apt.appointment_date}")
    print(f"  Time: {new_apt.time_slot}")


def demo_record_payment() -> None:
    """Record a sample payment."""
    db = DatabaseManager()
    billing_crud = BillingCRUD(db)

    print_header("RECORD PAYMENT - DEMO")

    # Get first unpaid bill
    unpaid = billing_crud.read_unpaid()

    if not unpaid:
        print("No unpaid bills to demonstrate payment recording.")
        return

    bill = unpaid[0]
    payment_amount = bill['total_amount'] * 0.5  # Pay 50%

    affected = billing_crud.record_payment(bill['bill_id'], payment_amount)

    if affected > 0:
        print(f"✓ Payment recorded successfully!")
        print(f"  Bill ID: {bill['bill_id']}")
        print(f"  Patient: {bill['patient_name']}")
        print(f"  Amount Paid: ₹{payment_amount:,.0f}")
        print(f"  Previous Paid: ₹{bill['paid_amount']:,.0f}")
        print(f"  New Total Paid: ₹{bill['paid_amount'] + payment_amount:,.0f}")
        print(f"  Total Amount: ₹{bill['total_amount']:,.0f}")
    else:
        print("Failed to record payment.")


def main_menu() -> None:
    """Display interactive main menu."""
    while True:
        print("\n" + "="*70)
        print("  HOSPITAL MANAGEMENT SYSTEM - MAIN MENU")
        print("="*70)
        print("\n1. View Patients Summary")
        print("2. View Upcoming Appointments")
        print("3. View Billing & Revenue")
        print("4. View Ward Occupancy")
        print("5. View Statistics Dashboard")
        print("6. Create New Appointment (Demo)")
        print("7. Record Payment (Demo)")
        print("8. Reset Database")
        print("9. Exit")

        choice = input("\nEnter your choice (1-9): ").strip()

        try:
            if choice == "1":
                display_patients_summary()
            elif choice == "2":
                display_appointments_summary()
            elif choice == "3":
                display_billing_summary()
            elif choice == "4":
                display_ward_occupancy()
            elif choice == "5":
                display_statistics()
            elif choice == "6":
                demo_create_appointment()
            elif choice == "7":
                demo_record_payment()
            elif choice == "8":
                confirm = input("\nAre you sure you want to reset the database? (yes/no): ").strip().lower()
                if confirm == "yes":
                    db = DatabaseManager()
                    db.reset_database()
                    print("✓ Database reset successfully!")
            elif choice == "9":
                print("\n✓ Thank you for using HMS. Goodbye!")
                break
            else:
                print("\n✗ Invalid choice. Please try again.")
        except Exception as e:
            print(f"\n✗ Error: {e}")
        except KeyboardInterrupt:
            print("\n\n✓ Program interrupted. Goodbye!")
            break


def quick_demo() -> None:
    """Run a quick demonstration of the system."""
    print_header("HOSPITAL MANAGEMENT SYSTEM - QUICK DEMO")

    # Initialize database
    print("Initializing database...")
    db = initialize_database()

    # Display all sections
    display_statistics()
    display_patients_summary()
    display_appointments_summary()
    display_ward_occupancy()
    display_billing_summary()

    print_header("✓ DEMO COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run quick demo
        quick_demo()
    else:
        # Initialize database
        print("\nInitializing Hospital Management System...")
        initialize_database()
        print("✓ Database initialized successfully!\n")

        # Start interactive menu
        try:
            main_menu()
        except KeyboardInterrupt:
            print("\n\n✓ Program interrupted. Goodbye!")
