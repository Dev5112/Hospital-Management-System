"""
Hospital Management System - SQL Query Constants
Common SQL queries for HMS operations.
"""

# ============================================================================
# PATIENT QUERIES
# ============================================================================

# Get all patients
GET_ALL_PATIENTS = """
    SELECT * FROM patients ORDER BY created_at DESC
"""

# Get patient by ID
GET_PATIENT_BY_ID = """
    SELECT * FROM patients WHERE patient_id = ?
"""

# Get patient by phone
GET_PATIENT_BY_PHONE = """
    SELECT * FROM patients WHERE phone = ?
"""

# Search patients by name
SEARCH_PATIENTS_BY_NAME = """
    SELECT * FROM patients WHERE name LIKE ? ORDER BY name
"""

# Insert new patient
INSERT_PATIENT = """
    INSERT INTO patients (name, dob, gender, phone, address, blood_group)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# Update patient
UPDATE_PATIENT = """
    UPDATE patients SET name = ?, dob = ?, gender = ?, phone = ?, address = ?, blood_group = ?
    WHERE patient_id = ?
"""

# Delete patient
DELETE_PATIENT = """
    DELETE FROM patients WHERE patient_id = ?
"""

# ============================================================================
# DOCTOR QUERIES
# ============================================================================

# Get all doctors
GET_ALL_DOCTORS = """
    SELECT * FROM doctors ORDER BY name
"""

# Get doctor by ID
GET_DOCTOR_BY_ID = """
    SELECT * FROM doctors WHERE doctor_id = ?
"""

# Get doctors by specialization
GET_DOCTORS_BY_SPECIALIZATION = """
    SELECT * FROM doctors WHERE specialization = ? ORDER BY name
"""

# Get available doctors
GET_AVAILABLE_DOCTORS = """
    SELECT DISTINCT d.* FROM doctors d
    WHERE d.available_days LIKE ?
    ORDER BY d.specialization, d.name
"""

# Insert new doctor
INSERT_DOCTOR = """
    INSERT INTO doctors (name, specialization, phone, email, available_days)
    VALUES (?, ?, ?, ?, ?)
"""

# Update doctor
UPDATE_DOCTOR = """
    UPDATE doctors SET name = ?, specialization = ?, phone = ?, email = ?, available_days = ?
    WHERE doctor_id = ?
"""

# ============================================================================
# APPOINTMENT QUERIES
# ============================================================================

# Get all appointments
GET_ALL_APPOINTMENTS = """
    SELECT * FROM appointments ORDER BY appointment_date DESC
"""

# Get appointments for patient
GET_APPOINTMENTS_BY_PATIENT = """
    SELECT a.*, p.name as patient_name, d.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE a.patient_id = ?
    ORDER BY a.appointment_date DESC
"""

# Get appointments for doctor
GET_APPOINTMENTS_BY_DOCTOR = """
    SELECT a.*, p.name as patient_name, d.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE a.doctor_id = ?
    ORDER BY a.appointment_date DESC
"""

# Get appointments by date range
GET_APPOINTMENTS_BY_DATE_RANGE = """
    SELECT a.*, p.name as patient_name, d.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE a.appointment_date BETWEEN ? AND ?
    ORDER BY a.appointment_date, a.time_slot
"""

# Get appointments for today
GET_APPOINTMENTS_TODAY = """
    SELECT a.*, p.name as patient_name, d.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE DATE(a.appointment_date) = DATE('now')
    ORDER BY a.time_slot
"""

# Insert new appointment
INSERT_APPOINTMENT = """
    INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status, notes)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# Update appointment status
UPDATE_APPOINTMENT_STATUS = """
    UPDATE appointments SET status = ? WHERE appointment_id = ?
"""

# Cancel appointment
CANCEL_APPOINTMENT = """
    UPDATE appointments SET status = 'cancelled' WHERE appointment_id = ?
"""

# ============================================================================
# WARD QUERIES
# ============================================================================

# Get all wards
GET_ALL_WARDS = """
    SELECT * FROM wards ORDER BY ward_type, ward_name
"""

# Get ward by ID
GET_WARD_BY_ID = """
    SELECT * FROM wards WHERE ward_id = ?
"""

# Get wards by type
GET_WARDS_BY_TYPE = """
    SELECT * FROM wards WHERE ward_type = ? ORDER BY ward_name
"""

# Get available wards (with beds)
GET_AVAILABLE_WARDS = """
    SELECT * FROM wards WHERE available_beds > 0 ORDER BY ward_type, ward_name
"""

# Get ward occupancy
GET_WARD_OCCUPANCY = """
    SELECT ward_id, ward_name, total_beds, available_beds,
           (total_beds - available_beds) as occupied_beds,
           ROUND((total_beds - available_beds) * 100.0 / total_beds, 2) as occupancy_rate
    FROM wards
    ORDER BY occupancy_rate DESC
"""

# Update ward available beds
UPDATE_WARD_BEDS = """
    UPDATE wards SET available_beds = ? WHERE ward_id = ?
"""

# ============================================================================
# ADMISSION QUERIES
# ============================================================================

# Get all admissions
GET_ALL_ADMISSIONS = """
    SELECT a.*, p.name as patient_name, w.ward_name, d.name as doctor_name
    FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN wards w ON a.ward_id = w.ward_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    ORDER BY a.admission_date DESC
"""

# Get active admissions
GET_ACTIVE_ADMISSIONS = """
    SELECT a.*, p.name as patient_name, w.ward_name, d.name as doctor_name
    FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN wards w ON a.ward_id = w.ward_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE a.status = 'admitted'
    ORDER BY a.admission_date DESC
"""

# Get admissions for patient
GET_ADMISSIONS_BY_PATIENT = """
    SELECT a.*, p.name as patient_name, w.ward_name, d.name as doctor_name
    FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN wards w ON a.ward_id = w.ward_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE a.patient_id = ?
    ORDER BY a.admission_date DESC
"""

# Insert new admission
INSERT_ADMISSION = """
    INSERT INTO admissions (patient_id, ward_id, doctor_id, admission_date, diagnosis, status)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# Discharge patient
DISCHARGE_ADMISSION = """
    UPDATE admissions SET status = 'discharged', discharge_date = ? WHERE admission_id = ?
"""

# ============================================================================
# BILLING QUERIES
# ============================================================================

# Get all bills
GET_ALL_BILLS = """
    SELECT * FROM billing ORDER BY created_at DESC
"""

# Get bills for patient
GET_BILLS_BY_PATIENT = """
    SELECT * FROM billing WHERE patient_id = ? ORDER BY created_at DESC
"""

# Get pending bills
GET_PENDING_BILLS = """
    SELECT b.*, p.name as patient_name
    FROM billing b
    JOIN patients p ON b.patient_id = p.patient_id
    WHERE b.payment_status IN ('pending', 'partial')
    ORDER BY b.created_at DESC
"""

# Get total revenue by payment status
GET_REVENUE_SUMMARY = """
    SELECT payment_status, COUNT(*) as bill_count, SUM(total_amount) as total_amount
    FROM billing
    GROUP BY payment_status
"""

# Insert new bill
INSERT_BILL = """
    INSERT INTO billing (patient_id, admission_id, total_amount, paid_amount, payment_status)
    VALUES (?, ?, ?, ?, ?)
"""

# Update bill payment
UPDATE_BILL_PAYMENT = """
    UPDATE billing SET paid_amount = ?, payment_status = ?, payment_date = ?
    WHERE bill_id = ?
"""

# ============================================================================
# STAFF QUERIES
# ============================================================================

# Get all staff
GET_ALL_STAFF = """
    SELECT * FROM staff ORDER BY department, shift, name
"""

# Get staff by department
GET_STAFF_BY_DEPARTMENT = """
    SELECT * FROM staff WHERE department = ? ORDER BY shift, name
"""

# Get staff by shift
GET_STAFF_BY_SHIFT = """
    SELECT * FROM staff WHERE shift = ? ORDER BY department, name
"""

# ============================================================================
# MEDICAL RECORDS QUERIES
# ============================================================================

# Get medical records for patient
GET_MEDICAL_RECORDS_BY_PATIENT = """
    SELECT mr.*, p.name as patient_name, d.name as doctor_name
    FROM medical_records mr
    JOIN patients p ON mr.patient_id = p.patient_id
    JOIN doctors d ON mr.doctor_id = d.doctor_id
    WHERE mr.patient_id = ?
    ORDER BY mr.visit_date DESC
"""

# Get medical records by date range
GET_MEDICAL_RECORDS_BY_DATE_RANGE = """
    SELECT mr.*, p.name as patient_name, d.name as doctor_name
    FROM medical_records mr
    JOIN patients p ON mr.patient_id = p.patient_id
    JOIN doctors d ON mr.doctor_id = d.doctor_id
    WHERE mr.visit_date BETWEEN ? AND ?
    ORDER BY mr.visit_date DESC
"""

# Insert new medical record
INSERT_MEDICAL_RECORD = """
    INSERT INTO medical_records (patient_id, doctor_id, visit_date, diagnosis, prescription, notes)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# ============================================================================
# ANALYTICS & REPORTING QUERIES
# ============================================================================

# Get patient visit history
GET_PATIENT_VISIT_HISTORY = """
    SELECT mr.* FROM medical_records mr
    WHERE mr.patient_id = ?
    ORDER BY mr.visit_date DESC
"""

# Get doctor schedule
GET_DOCTOR_SCHEDULE = """
    SELECT d.*, COUNT(a.appointment_id) as appointments_count
    FROM doctors d
    LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
    WHERE DATE(a.appointment_date) = ?
    GROUP BY d.doctor_id
"""

# Get patient length of stay
GET_PATIENT_LENGTH_OF_STAY = """
    SELECT admission_id, patient_id,
           CAST((julianday(COALESCE(discharge_date, 'now')) - julianday(admission_date)) AS INTEGER) as days_admitted
    FROM admissions
    WHERE status = 'discharged'
"""

# Get monthly admission statistics
GET_MONTHLY_ADMISSION_STATS = """
    SELECT strftime('%Y-%m', admission_date) as month,
           COUNT(*) as admission_count
    FROM admissions
    GROUP BY strftime('%Y-%m', admission_date)
    ORDER BY month DESC
"""

# Get doctor performance metrics
GET_DOCTOR_PERFORMANCE = """
    SELECT d.doctor_id, d.name, d.specialization,
           COUNT(a.appointment_id) as total_appointments,
           SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed_appointments
    FROM doctors d
    LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
    GROUP BY d.doctor_id
    ORDER BY completed_appointments DESC
"""
