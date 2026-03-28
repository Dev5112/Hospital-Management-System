# Hospital Management System (HMS) - Database Setup Guide

## Project Overview
A complete Hospital Management System with SQLite3 database, featuring 8 interconnected tables with proper constraints, foreign keys, and comprehensive CRUD operations.

## File Structure

### Core Files
1. **database.py** (17 KB)
   - `DatabaseManager` class handles all database operations
   - Methods: `create_tables()`, `seed_data()`, `reset_database()`, `get_db_stats()`
   - Context manager support for safe connection handling
   - Foreign key constraints enabled

2. **models.py** (3.7 KB)
   - Dataclasses for all 8 entities
   - Patient, Doctor, Appointment, Ward, Admission, Billing, Staff, MedicalRecord
   - Type hints and property methods

3. **queries.py** (11 KB)
   - 50+ SQL query constants organized by table
   - Common operations pre-written
   - Analytics and reporting queries included

4. **crud_operations.py** (15 KB)
   - CRUD examples for Patient and Appointment tables
   - PatientCRUD, AppointmentCRUD, BillingCRUD classes
   - Methods: create, read, read_all, search, update, delete

5. **utils.py** (8+ KB)
   - ReportGenerator: Ward census, revenue, doctor performance reports
   - ValidationHelper: Data validation utilities
   - BackupRestore: Database backup and JSON export
   - DataValidator: Referential integrity checking

6. **hms_example.py** (6.7 KB)
   - Comprehensive demonstration script
   - Shows all major operations
   - Generates formatted reports and statistics

## Database Schema

### Tables (8 total with 30+ indexes)

#### 1. patients
- Patient demographics and health info
- Indexes: phone, name
- Constraints: UNIQUE phone, CHECK on gender and blood_group

#### 2. doctors
- Doctor profiles and specializations
- Indexes: phone, specialization
- Constraints: UNIQUE phone, UNIQUE email

#### 3. appointments
- Daily appointment scheduling
- Foreign Keys: patient_id, doctor_id
- Indexes: patient_id, doctor_id, appointment_date
- Constraints: CHECK on status

#### 4. wards
- Hospital ward management
- Indexes: ward_type
- Constraints: CHECK on bed counts

#### 5. admissions
- Patient hospital admissions
- Foreign Keys: patient_id, ward_id, doctor_id
- Constraints: CHECK on status (admitted/discharged/transferred)

#### 6. billing
- Patient billing and payments
- Foreign Keys: patient_id, admission_id
- Constraints: CHECK on amounts and payment status

#### 7. staff
- Staff member information
- Indexes: department, shift
- Constraints: UNIQUE phone

#### 8. medical_records
- Patient medical history
- Foreign Keys: patient_id, doctor_id
- Indexes: patient_id, visit_date

## Quick Start

### 1. Initialize Database
```python
from database import DatabaseManager

db_manager = DatabaseManager("hms_database.db")
db_manager.create_tables()
db_manager.seed_data()
```

### 2. Use CRUD Operations
```python
from crud_operations import PatientCRUD
from models import Patient

patient_crud = PatientCRUD(db_manager)

# Create
new_patient = Patient(name="John Doe", dob="1990-01-01", ...)
patient_id = patient_crud.create(new_patient)

# Read
patient = patient_crud.read(patient_id)

# Update
patient.phone = "9999888888"
patient_crud.update(patient)

# Delete
patient_crud.delete(patient_id)
```

### 3. Execute Queries
```python
from queries import GET_APPOINTMENTS_TODAY

with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(GET_APPOINTMENTS_TODAY)
    appointments = cursor.fetchall()
```

### 4. Generate Reports
```python
from utils import ReportGenerator

report_gen = ReportGenerator(db_manager)
census = report_gen.ward_census_report()
revenue = report_gen.monthly_revenue_report()
workload = report_gen.doctor_workload_report()
```

## Key Features

✓ **Proper Foreign Key Constraints** - Referential integrity maintained
✓ **Foreign Key Support** - PRAGMA enabled in all connections
✓ **Comprehensive Indexes** - Optimized for common queries
✓ **Data Validation** - Constraints on all fields
✓ **Seed Data** - 5 patients, 5 doctors, 5 wards pre-populated
✓ **Context Managers** - Safe database connection handling
✓ **Transaction Support** - Automatic commit/rollback
✓ **Type Hints** - Full type annotations for IDE support
✓ **Sample Data** - Real-world healthcare scenarios
✓ **Reporting Tools** - Built-in analytics and exports

## Dependencies
- Python 3.6+
- sqlite3 (built-in, no external dependencies)

## Running Examples

### Basic Demo
```bash
python3 hms_example.py
```

### Test Database Operations
```bash
python3 crud_operations.py
```

### Generate Reports
```bash
python3 utils.py
```

## Production Considerations

1. **Backup Strategy**: Use `BackupRestore.backup_database()`
2. **Data Export**: JSON export available via `export_data_json()`
3. **Validation**: Run `DataValidator` before critical operations
4. **Connection Pool**: Implement pooling for multi-threaded access
5. **Indexes**: Additional indexes can be added as query patterns emerge
6. **Archival**: Consider partitioning old medical records by year

## SQL Examples

```sql
-- Get today's appointments
SELECT a.*, p.name, d.name FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN doctors d ON a.doctor_id = d.doctor_id
WHERE DATE(a.appointment_date) = DATE('now');

-- Ward occupancy report
SELECT ward_name, total_beds, available_beds,
       ROUND((total_beds - available_beds) * 100.0 / total_beds, 2) as occupancy_rate
FROM wards;

-- Patient billing history
SELECT b.*, p.name FROM billing b
JOIN patients p ON b.patient_id = p.patient_id
WHERE p.patient_id = ?
ORDER BY b.created_at DESC;
```

## License
Educational Use - Hospital Management System Database Template
