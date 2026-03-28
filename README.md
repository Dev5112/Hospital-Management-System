# Hospital Management System (HMS) - SQLite3 Database Setup

A production-ready Hospital Management System built with Python and SQLite3. Includes complete database schema, models, CRUD operations, and example usage.

## Features

✅ **8 Interconnected Tables** with proper foreign key relationships
✅ **Data Validation** using dataclasses with post-initialization checks
✅ **Complete CRUD Operations** for all entities
✅ **Advanced SQL Queries** for reporting and analytics
✅ **Context Managers** for safe database transactions
✅ **Seed Data** for testing and development
✅ **Comprehensive Indexes** for optimized queries
✅ **Production-Ready Code** with docstrings and error handling

## Project Structure

```
.
├── database.py          # DatabaseManager class, table creation, data seeding
├── models.py            # Dataclasses for all entities
├── queries.py           # SQL query constants organized by entity
├── crud.py              # CRUD operation classes for Patient, Appointment, Billing
├── main.py              # Main application with interactive menu
└── hms.db               # SQLite database file (generated)
```

## Database Schema

### Tables Overview

1. **patients** - Patient information
   - Primary Key: `patient_id`
   - Unique: `phone`
   - Validation: gender, blood_group

2. **doctors** - Medical practitioners
   - Primary Key: `doctor_id`
   - Unique: `phone`, `email`
   - Indexes: specialization, phone

3. **appointments** - Patient-Doctor appointments
   - Primary Key: `appointment_id`
   - Foreign Keys: `patient_id` (CASCADE), `doctor_id` (RESTRICT)
   - Indexes: patient, doctor, date, status

4. **wards** - Hospital wards/departments
   - Primary Key: `ward_id`
   - Validation: ward_type (General/ICU/Private), bed counts
   - Indexes: type

5. **admissions** - Patient hospital admissions
   - Primary Key: `admission_id`
   - Foreign Keys: patient, ward, doctor
   - Status tracking: Active/Discharged/Transferred

6. **billing** - Patient billing and payments
   - Primary Key: `bill_id`
   - Foreign Keys: patient, admission (optional)
   - Payment tracking with validation

7. **staff** - Hospital staff information
   - Primary Key: `staff_id`
   - Role and shift management
   - Indexes: department, role

8. **medical_records** - Patient medical history
   - Primary Key: `record_id`
   - Foreign Keys: patient, doctor
   - Visit records with diagnosis and prescription

## Installation

### Prerequisites
- Python 3.7+
- No external dependencies (uses built-in `sqlite3`)

### Setup

```bash
# Clone or navigate to your project directory
cd MAD1\ Proj

# Run the main application
python main.py

# Or run quick demo
python main.py --demo

# Test CRUD operations
python crud.py
```

## Usage Examples

### Initialize Database

```python
from database import initialize_database

db = initialize_database()  # Creates tables and seeds sample data
```

### Patient Operations

```python
from database import DatabaseManager
from crud import PatientCRUD
from models import Patient
from datetime import date

db = DatabaseManager()
patient_crud = PatientCRUD(db)

# Create a patient
new_patient = Patient(
    name="John Doe",
    dob=date(1985, 3, 15),
    gender="Male",
    phone="9876543210",
    address="123 Main St, City",
    blood_group="O+"
)
patient_id = patient_crud.create(new_patient)

# Read a patient
patient = patient_crud.read(patient_id)

# Search by name
results = patient_crud.search_by_name("John")

# Get all patients
all_patients = patient_crud.read_all()

# Update patient
new_patient.patient_id = patient_id
new_patient.address = "Updated address"
patient_crud.update(new_patient)
```

### Appointment Operations

```python
from crud import AppointmentCRUD
from models import Appointment
from datetime import date, timedelta

apt_crud = AppointmentCRUD(db)

# Create appointment
new_apt = Appointment(
    patient_id=1,
    doctor_id=1,
    appointment_date=date.today() + timedelta(days=3),
    time_slot="09:00 AM",
    status="Scheduled",
    notes="Regular checkup"
)
apt_id = apt_crud.create(new_apt)

# Get upcoming appointments
upcoming = apt_crud.read_upcoming()

# Update appointment status
apt_crud.update_status(apt_id, "Completed", "Checkup completed")

# Cancel appointment
apt_crud.cancel(apt_id)
```

### Billing Operations

```python
from crud import BillingCRUD
from models import Billing

billing_crud = BillingCRUD(db)

# Create bill
new_bill = Billing(
    patient_id=1,
    admission_id=1,
    total_amount=50000.0,
    paid_amount=0.0,
    payment_status="Pending"
)
bill_id = billing_crud.create(new_bill)

# Record payment
billing_crud.record_payment(bill_id, 25000.0)  # Pay 25000

# Get financial summary
total_revenue = billing_crud.get_total_revenue()
pending_amount = billing_crud.get_pending_amount()
```

### Direct SQL Queries

```python
from database import DatabaseManager
import queries

db = DatabaseManager()

# Get all doctors by specialization
cardiologists = db.execute_query(
    queries.SELECT_DOCTORS_BY_SPECIALIZATION,
    ("Cardiology",)
)

# Get active admissions
active = db.execute_query(queries.SELECT_ACTIVE_ADMISSIONS)

# Get ward occupancy
occupancy = db.execute_query(queries.WARD_OCCUPANCY)

# Get statistics
stats = db.execute_query(queries.STATISTICS_SUMMARY)
```

## API Reference

### DatabaseManager

#### Methods

- `get_connection()` - Context manager for database connections
  ```python
  with db.get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute(query)
  ```

- `create_tables()` - Create all database tables with indexes

- `seed_data()` - Populate with sample data for testing

- `execute_query(query, params)` - Execute SELECT queries
  - Returns: `List[Tuple]`

- `execute_write_query(query, params)` - Execute INSERT/UPDATE/DELETE
  - Returns: `int` (rows affected)

- `reset_database()` - Drop all tables and recreate (⚠️ destructive)

### PatientCRUD

- `create(patient)` - Create new patient
- `read(patient_id)` - Get patient by ID
- `read_by_phone(phone)` - Get patient by phone
- `read_all()` - Get all patients
- `search_by_name(name)` - Search by name (partial match)
- `search_by_blood_group(blood_group)` - Search by blood group
- `update(patient)` - Update patient data
- `delete(patient_id)` - Delete patient
- `count()` - Get total patient count

### AppointmentCRUD

- `create(appointment)` - Create new appointment
- `read_by_patient(patient_id)` - Get appointments for patient
- `read_by_doctor(doctor_id)` - Get appointments for doctor
- `read_by_date(date)` - Get appointments for date
- `read_upcoming()` - Get all upcoming appointments
- `read_all()` - Get all appointments
- `update_status(id, status, notes)` - Update appointment
- `cancel(id)` - Cancel appointment
- `delete(id)` - Delete appointment

### BillingCRUD

- `create(billing)` - Create new bill
- `read_by_patient(patient_id)` - Get bills for patient
- `read_unpaid()` - Get unpaid/partial bills
- `read_all()` - Get all bills
- `record_payment(bill_id, amount)` - Record payment
- `get_total_revenue()` - Get total paid amount
- `get_pending_amount()` - Get total pending amount

## Data Models (Dataclasses)

### Patient
```python
@dataclass
class Patient:
    name: str
    dob: date
    gender: str  # 'Male', 'Female', 'Other'
    phone: str
    address: str
    blood_group: Optional[str]  # 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
    patient_id: Optional[int] = None
    created_at: Optional[datetime] = None
```

### Appointment
```python
@dataclass
class Appointment:
    patient_id: int
    doctor_id: int
    appointment_date: date
    time_slot: str
    status: str = "Scheduled"  # 'Scheduled', 'Completed', 'Cancelled'
    notes: Optional[str] = None
    appointment_id: Optional[int] = None
    created_at: Optional[datetime] = None
```

### Billing
```python
@dataclass
class Billing:
    patient_id: int
    total_amount: float
    paid_amount: float = 0.0
    payment_status: str = "Pending"  # 'Pending', 'Paid', 'Partial'
    admission_id: Optional[int] = None
    payment_date: Optional[datetime] = None
    bill_id: Optional[int] = None
    created_at: Optional[datetime] = None
```

See `models.py` for all dataclass definitions.

## SQL Queries Available

All queries are defined as constants in `queries.py`:

### Patient Queries
- `SELECT_ALL_PATIENTS`
- `SELECT_PATIENT_BY_ID`
- `SELECT_PATIENT_BY_PHONE`
- `SEARCH_PATIENTS_BY_NAME`
- `SEARCH_PATIENTS_BY_BLOOD_GROUP`
- `COUNT_PATIENTS`

### Appointment Queries
- `SELECT_ALL_APPOINTMENTS`
- `SELECT_APPOINTMENTS_BY_PATIENT`
- `SELECT_APPOINTMENTS_BY_DOCTOR`
- `SELECT_APPOINTMENTS_BY_DATE`
- `SELECT_UPCOMING_APPOINTMENTS`

### Billing Queries
- `SELECT_ALL_BILLS`
- `SELECT_BILLS_BY_PATIENT`
- `SELECT_UNPAID_BILLS`
- `CALCULATE_TOTAL_REVENUE`
- `CALCULATE_PENDING_PAYMENTS`

### Reporting Queries
- `WARD_OCCUPANCY`
- `STATISTICS_SUMMARY`
- `DOCTOR_APPOINTMENTS_COUNT`
- `REVENUE_BY_MONTH`
- `PATIENTS_ADMITTED_TODAY`
- `PATIENTS_DISCHARGED_TODAY`

See `queries.py` for the complete list of 70+ queries.

## Best Practices Implemented

✅ **Foreign Key Constraints** - Referential integrity with CASCADE/RESTRICT rules
✅ **Indexes** - On frequently queried columns (phone, email, dates, status)
✅ **Constraints** - CHECK constraints for valid enums and ranges
✅ **Context Managers** - Automatic connection and transaction management
✅ **Data Validation** - Using dataclass `__post_init__` methods
✅ **Parameterized Queries** - Protection against SQL injection
✅ **Docstrings** - Complete documentation for all methods
✅ **Type Hints** - Type annotations for better code clarity
✅ **Error Handling** - Try-except blocks with meaningful messages
✅ **Sample Data** - Realistic seed data for testing

## Running the Application

### Interactive Menu
```bash
python main.py
```

Features:
- View Patients Summary
- View Upcoming Appointments
- View Billing & Revenue
- View Ward Occupancy
- View Statistics Dashboard
- Create/Update/Delete operations
- Payment recording
- Database reset

### Quick Demo
```bash
python main.py --demo
```

Displays:
- Database initialization
- Statistics overview
- Sample data
- All main features

### CRUD Testing
```bash
python crud.py
```

Runs comprehensive tests of all CRUD operations.

## Database File

The database is stored as `hms.db` in the project directory.

- **Size**: ~50 KB with sample data
- **Connection**: Uses `sqlite3` connection pooling via context managers
- **Backup**: Simply copy `hms.db` to backup

## Common Patterns

### Safe Database Operations
```python
from database import DatabaseManager

db = DatabaseManager()

# Always use context manager
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(query, params)
    # Auto-committed on success, rolled back on error
```

### Validation Before Insert
```python
from models import Patient

try:
    patient = Patient(
        name="John",
        dob=date(1990, 5, 1),
        gender="Male",  # Validated
        phone="9876543210",
        address="123 Main",
        blood_group="O+"  # Validated
    )
    patient_id = patient_crud.create(patient)
except ValueError as e:
    print(f"Invalid data: {e}")
```

### Query with Parameters
```python
# Safe from SQL injection
results = db.execute_query(
    "SELECT * FROM patients WHERE phone = ?",
    (phone_number,)
)
```

## Troubleshooting

### Database locked error
- Ensure connections are properly closed using context managers
- Check no other processes have the database open

### Foreign key constraint violation
- Verify parent records exist before inserting child records
- Check CASCADE/RESTRICT rules in schema

### Invalid enum error
- Check allowed values in model dataclass `__post_init__`
- Refer to schema comments for valid values

## Future Enhancements

Possible extensions:
- User authentication and role-based access control
- Appointment scheduling with conflict detection
- Automated billing calculations
- Patient history timeline
- Staff schedule management
- Medication inventory tracking
- Emergency alert system
- Multi-location support

## License

This is a sample project for educational purposes.

## Support

For issues or questions about the implementation:
1. Check the docstrings in each module
2. Review example usage in `main.py` and `crud.py`
3. Refer to SQL queries in `queries.py`
4. Check data models in `models.py`

---

**Version**: 1.0
**Last Updated**: 2026-03-28
**Built With**: Python 3.7+, SQLite3
