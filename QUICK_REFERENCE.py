"""
Hospital Management System - Quick Reference Guide
Easy copy-paste examples for common operations.
"""

# ==================== INITIALIZATION ====================

from database import initialize_database, DatabaseManager
from crud import PatientCRUD, AppointmentCRUD, BillingCRUD
from models import Patient, Appointment, Billing, Doctor, Ward, Admission, Staff, MedicalRecord
from datetime import date, datetime, timedelta
import queries

# Initialize the database (creates tables and seed data)
db = initialize_database()
# Output: ✓ Hospital Management System database initialized successfully!


# ==================== PATIENT OPERATIONS ====================

patient_crud = PatientCRUD(db)

# Create a new patient
new_patient = Patient(
    name="John Smith",
    dob=date(1990, 5, 15),
    gender="Male",
    phone="9800000001",
    address="456 Park Ave, City",
    blood_group="B+"
)
patient_id = patient_crud.create(new_patient)
print(f"Created patient ID: {patient_id}")

# Get a patient by ID
patient = patient_crud.read(patient_id)
print(f"Patient: {patient['name']}, Phone: {patient['phone']}")

# Get all patients
all_patients = patient_crud.read_all()
print(f"Total patients: {len(all_patients)}")

# Search patients by name
search_results = patient_crud.search_by_name("John")
print(f"Patients named John: {len(search_results)}")

# Search patients by blood group
blood_group_results = patient_crud.search_by_blood_group("O+")
print(f"O+ blood group patients: {len(blood_group_results)}")

# Get patient by phone
patient_by_phone = patient_crud.read_by_phone("9876543210")
print(f"Patient phone lookup: {patient_by_phone['name']}")

# Update patient (must set patient_id)
new_patient.patient_id = patient_id
new_patient.address = "999 New Location, City"
rows_affected = patient_crud.update(new_patient)

# Delete patient
deleted = patient_crud.delete(patient_id)

# Count all patients
total = patient_crud.count()
print(f"Total patients in system: {total}")


# ==================== APPOINTMENT OPERATIONS ====================

apt_crud = AppointmentCRUD(db)

# Create a new appointment
new_apt = Appointment(
    patient_id=1,
    doctor_id=2,
    appointment_date=date.today() + timedelta(days=5),
    time_slot="02:30 PM",
    status="Scheduled",
    notes="Consultation for checkup"
)
apt_id = apt_crud.create(new_apt)
print(f"Created appointment ID: {apt_id}")

# Get appointments for a patient
patient_apts = apt_crud.read_by_patient(1)
print(f"Patient 1 has {len(patient_apts)} appointments")

# Get appointments for a doctor
doctor_apts = apt_crud.read_by_doctor(1)
print(f"Doctor 1 has {len(doctor_apts)} appointments")

# Get all appointments on a specific date
date_apts = apt_crud.read_by_date(date(2026, 3, 30))
print(f"Appointments on 2026-03-30: {len(date_apts)}")

# Get all upcoming appointments
upcoming = apt_crud.read_upcoming()
print(f"Total upcoming appointments: {len(upcoming)}")

# Get all appointments
all_apts = apt_crud.read_all()
print(f"Total appointments: {len(all_apts)}")

# Update appointment status
apt_crud.update_status(apt_id, "Completed", "Checkup completed")

# Cancel an appointment
apt_crud.cancel(apt_id)

# Delete an appointment
apt_crud.delete(apt_id)


# ==================== BILLING OPERATIONS ====================

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
print(f"Created bill ID: {bill_id}")

# Get bills for a patient
patient_bills = billing_crud.read_by_patient(1)
print(f"Patient 1 has {len(patient_bills)} bills")

# Get all unpaid bills
unpaid_bills = billing_crud.read_unpaid()
print(f"Unpaid bills: {len(unpaid_bills)}")

# Get all bills
all_bills = billing_crud.read_all()
print(f"Total bills: {len(all_bills)}")

# Record a payment (auto-updates status)
billing_crud.record_payment(bill_id, 25000.0)
print("Recorded payment of 25000")

# Get financial statistics
total_revenue = billing_crud.get_total_revenue()
pending = billing_crud.get_pending_amount()
print(f"Revenue: ₹{total_revenue}, Pending: ₹{pending}")

# Get bill details
bill_data = db.execute_query(queries.SELECT_BILL_BY_ID, (bill_id,))
print(f"Bill {bill_id} details: {dict(bill_data[0]) if bill_data else 'Not found'}")


# ==================== DIRECT SQL QUERIES ====================

# Get doctors by specialization
cardiologists = db.execute_query(
    queries.SELECT_DOCTORS_BY_SPECIALIZATION,
    ("Cardiology",)
)
print(f"Cardiologists: {len(cardiologists)}")

# Get all active admissions
active_admissions = db.execute_query(queries.SELECT_ACTIVE_ADMISSIONS)
print(f"Active admissions: {len(active_admissions)}")

# Get appointment count by doctor
doc_stats = db.execute_query(queries.DOCTOR_APPOINTMENTS_COUNT)
for stat in doc_stats:
    stat_dict = dict(stat)
    print(f"Dr. {stat_dict['name']}: {stat_dict['total_appointments']} appointments")

# Get ward occupancy
occupancy = db.execute_query(queries.WARD_OCCUPANCY)
for ward in occupancy:
    ward_dict = dict(ward)
    print(f"{ward_dict['ward_name']}: {ward_dict['occupancy_percentage']}% full")

# Get revenue by month
revenue_data = db.execute_query(queries.REVENUE_BY_MONTH)
for month_data in revenue_data:
    data_dict = dict(month_data)
    print(f"{data_dict['month']}: ₹{data_dict['total_paid']}")

# Get hospital statistics
stats = db.execute_query(queries.STATISTICS_SUMMARY)
if stats:
    stat_dict = dict(stats[0])
    print(f"Patients: {stat_dict['total_patients']}, "
          f"Doctors: {stat_dict['total_doctors']}, "
          f"Active Admissions: {stat_dict['active_admissions']}")


# ==================== ERROR HANDLING ====================

from models import Patient

try:
    # This will raise ValueError - invalid gender
    invalid_patient = Patient(
        name="Test",
        dob=date(1990, 1, 1),
        gender="InvalidGender",  # Invalid!
        phone="9999999999",
        address="Test",
        blood_group="O+"
    )
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # This will raise ValueError - invalid blood group
    invalid_patient = Patient(
        name="Test",
        dob=date(1990, 1, 1),
        gender="Male",
        phone="9999999999",
        address="Test",
        blood_group="XYZ"  # Invalid!
    )
except ValueError as e:
    print(f"Validation error: {e}")


# ==================== DATABASE MANAGEMENT ====================

# Reset database (drops and recreates all tables)
db.reset_database()

# Direct query execution
results = db.execute_query("SELECT * FROM patients WHERE patient_id = ?", (1,))

# Direct write query
rows_affected, last_id = db.execute_write_query(
    "INSERT INTO patients (name, dob, gender, phone, address, blood_group) VALUES (?, ?, ?, ?, ?, ?)",
    ("New Patient", date(1985, 1, 1), "Male", "9111111111", "Address", "O+")
)


# ==================== COMMON PATTERNS ====================

# Pattern 1: Safe database operations with context manager
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]
    print(f"Patient count (via context manager): {count}")

# Pattern 2: Batch insert
patients_list = [
    ("Patient A", date(1990, 1, 1), "Male", "9111111111", "Addr A", "O+"),
    ("Patient B", date(1990, 1, 2), "Female", "9111111112", "Addr B", "O-"),
    ("Patient C", date(1990, 1, 3), "Male", "9111111113", "Addr C", "A+"),
]
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO patients (name, dob, gender, phone, address, blood_group) VALUES (?, ?, ?, ?, ?, ?)",
        patients_list
    )

# Pattern 3: Transaction with rollback on error
try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients ...")
        cursor.execute("INSERT INTO appointments ...")
        # Both executed, both committed
except Exception as e:
    print(f"Transaction rolled back due to: {e}")

# Pattern 4: Search with LIKE
search_term = "John"
results = db.execute_query(
    "SELECT * FROM patients WHERE name LIKE ?",
    (f"%{search_term}%",)
)


# ==================== PERFORMANCE TIPS ====================

# Tips:
# 1. Use parameterized queries to prevent SQL injection
# 2. Always use context managers for connections
# 3. Use indexes (already created on frequently queried columns)
# 4. Batch operations when inserting many records
# 5. Use LIMIT in queries when you don't need all results
# 6. Profile queries for performance bottlenecks

# Example: Paginate results
limit = 10
offset = 0
paginated = db.execute_query(
    "SELECT * FROM patients ORDER BY created_at DESC LIMIT ? OFFSET ?",
    (limit, offset)
)


# ==================== BASIC SQL IF NEEDED ====================

# You can always write raw SQL if needed
custom_query = """
    SELECT p.name, COUNT(a.appointment_id) as appointment_count
    FROM patients p
    LEFT JOIN appointments a ON p.patient_id = a.patient_id
    GROUP BY p.patient_id
    ORDER BY appointment_count DESC
"""

results = db.execute_query(custom_query)
for row in results:
    row_dict = dict(row)
    print(f"{row_dict['name']}: {row_dict['appointment_count']} appointments")
