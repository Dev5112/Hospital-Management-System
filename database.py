"""
Hospital Management System - Database Setup
Handles SQLite3 database initialization, table creation, and seed data.
"""

import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, List, Tuple, Any
import os


class DatabaseManager:
    """Manages SQLite3 database operations for HMS with proper schema and constraints."""

    def __init__(self, db_path: str = "hms_database.db"):
        """
        Initialize the DatabaseManager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database with foreign key support enabled."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection with row factory set
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self) -> None:
        """Create all HMS database tables with proper constraints and indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # 1. PATIENTS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    dob DATE NOT NULL,
                    gender TEXT NOT NULL CHECK(gender IN ('M', 'F', 'Other')),
                    phone TEXT NOT NULL UNIQUE,
                    address TEXT,
                    blood_group TEXT CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name)")

            # 2. DOCTORS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialization TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    available_days TEXT DEFAULT 'Mon-Fri',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_phone ON doctors(phone)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors(specialization)")

            # 3. APPOINTMENTS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    appointment_date DATE NOT NULL,
                    time_slot TEXT NOT NULL,
                    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'completed', 'cancelled')),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE RESTRICT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)")

            # 4. WARDS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wards (
                    ward_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ward_name TEXT NOT NULL UNIQUE,
                    ward_type TEXT NOT NULL CHECK(ward_type IN ('general', 'ICU', 'private')),
                    total_beds INTEGER NOT NULL CHECK(total_beds > 0),
                    available_beds INTEGER NOT NULL CHECK(available_beds >= 0),
                    CHECK(available_beds <= total_beds)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wards_type ON wards(ward_type)")

            # 5. ADMISSIONS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admissions (
                    admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    ward_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    admission_date TIMESTAMP NOT NULL,
                    discharge_date TIMESTAMP,
                    diagnosis TEXT,
                    status TEXT DEFAULT 'admitted' CHECK(status IN ('admitted', 'discharged', 'transferred')),
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                    FOREIGN KEY (ward_id) REFERENCES wards(ward_id) ON DELETE RESTRICT,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE RESTRICT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_patient ON admissions(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_ward ON admissions(ward_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_status ON admissions(status)")

            # 6. BILLING TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS billing (
                    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    admission_id INTEGER,
                    total_amount DECIMAL(10, 2) NOT NULL CHECK(total_amount >= 0),
                    paid_amount DECIMAL(10, 2) DEFAULT 0 CHECK(paid_amount >= 0),
                    payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('pending', 'partial', 'paid')),
                    payment_date TIMESTAMP,
                    billing_code TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id) ON DELETE SET NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_patient ON billing(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_status ON billing(payment_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_code ON billing(billing_code)")

            # 7. STAFF TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staff (
                    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    department TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    shift TEXT CHECK(shift IN ('morning', 'evening', 'night')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_staff_department ON staff(department)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_staff_shift ON staff(shift)")

            # 8. MEDICAL_RECORDS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medical_records (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    visit_date TIMESTAMP NOT NULL,
                    diagnosis TEXT,
                    prescription TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE RESTRICT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_medical_records_patient ON medical_records(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_medical_records_date ON medical_records(visit_date)")

            # 9. DRUG_INTERACTIONS TABLE (for Ambient AI Scribe)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drug_interactions (
                    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug1 TEXT NOT NULL,
                    drug2 TEXT NOT NULL,
                    severity TEXT NOT NULL CHECK(severity IN ('warning', 'alert', 'critical')),
                    description TEXT,
                    UNIQUE(drug1, drug2)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drug_pairs ON drug_interactions(drug1, drug2)")

            # 10. BILLING_CODES TABLE (for Ambient AI Scribe - ICD-10/CPT codes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS billing_codes (
                    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    code_type TEXT NOT NULL,
                    description TEXT,
                    standard_amount DECIMAL(10, 2),
                    category TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_code ON billing_codes(code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_code_type ON billing_codes(code_type)")

            conn.commit()
            print("✓ All tables created successfully")

    def seed_data(self) -> None:
        """Populate database with sample data for testing and demonstration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM patients")
            if cursor.fetchone()[0] > 0:
                print("✓ Database already contains data. Skipping seed...")
                return

            # SEED PATIENTS
            patients = [
                ("Rajesh Kumar", "1985-03-15", "M", "9876543210", "123 Main St, Delhi", "O+"),
                ("Priya Singh", "1990-07-22", "F", "9876543211", "456 Oak Ave, Mumbai", "A+"),
                ("Amit Patel", "1978-11-08", "M", "9876543212", "789 Pine Rd, Bangalore", "B+"),
                ("Neha Sharma", "1988-05-30", "F", "9876543213", "321 Elm St, Pune", "AB-"),
                ("Vijay Desai", "1995-02-14", "M", "9876543214", "654 Birch Ln, Hyderabad", "O-"),
            ]
            cursor.executemany(
                "INSERT INTO patients (name, dob, gender, phone, address, blood_group) VALUES (?, ?, ?, ?, ?, ?)",
                patients
            )

            # SEED DOCTORS
            doctors = [
                ("Dr. Arjun Verma", "Cardiology", "8765432101", "arjun.verma@hospital.com", "Mon-Sat"),
                ("Dr. Lakshmi Nair", "Neurology", "8765432102", "lakshmi.nair@hospital.com", "Mon-Fri"),
                ("Dr. Suresh Iyer", "Orthopedics", "8765432103", "suresh.iyer@hospital.com", "Tue-Sat"),
                ("Dr. Meera Das", "Pediatrics", "8765432104", "meera.das@hospital.com", "Mon-Thu"),
                ("Dr. Rohan Gupta", "General Practice", "8765432105", "rohan.gupta@hospital.com", "Mon-Fri"),
            ]
            cursor.executemany(
                "INSERT INTO doctors (name, specialization, phone, email, available_days) VALUES (?, ?, ?, ?, ?)",
                doctors
            )

            # SEED WARDS
            wards = [
                ("General Ward A", "general", 30, 15),
                ("General Ward B", "general", 25, 10),
                ("ICU Ward", "ICU", 10, 2),
                ("Private Ward", "private", 8, 4),
                ("Pediatric Ward", "general", 20, 8),
            ]
            cursor.executemany(
                "INSERT INTO wards (ward_name, ward_type, total_beds, available_beds) VALUES (?, ?, ?, ?)",
                wards
            )

            # SEED APPOINTMENTS
            today = datetime.now().date()
            appointments = [
                (1, 1, today + timedelta(days=2), "10:00 AM", "scheduled", "Regular checkup"),
                (2, 2, today + timedelta(days=3), "02:30 PM", "scheduled", "Follow-up consultation"),
                (3, 3, today + timedelta(days=1), "11:00 AM", "completed", "Post-surgery review"),
                (4, 4, today + timedelta(days=5), "03:00 PM", "scheduled", "Pediatric consultation"),
                (5, 5, today, "04:00 PM", "scheduled", "General health check"),
            ]
            cursor.executemany(
                "INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                appointments
            )

            # SEED ADMISSIONS
            admission_date = datetime.now() - timedelta(days=5)
            discharge_date = datetime.now() - timedelta(days=2)
            admissions = [
                (1, 1, 1, admission_date, discharge_date, "Hypertension management", "discharged"),
                (2, 2, 3, datetime.now() - timedelta(days=1), None, "Migraine treatment", "admitted"),
                (3, 3, 2, datetime.now() - timedelta(days=10), datetime.now() - timedelta(days=7), "Orthopedic surgery recovery", "discharged"),
            ]
            cursor.executemany(
                "INSERT INTO admissions (patient_id, ward_id, doctor_id, admission_date, discharge_date, diagnosis, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                admissions
            )

            # SEED BILLING
            billing = [
                (1, 1, 15000.00, 15000.00, "paid", datetime.now() - timedelta(days=2)),
                (2, 2, 8500.00, 5000.00, "partial", datetime.now() - timedelta(days=1)),
                (3, 3, 45000.00, 0.00, "pending", None),
            ]
            cursor.executemany(
                "INSERT INTO billing (patient_id, admission_id, total_amount, paid_amount, payment_status, payment_date) VALUES (?, ?, ?, ?, ?, ?)",
                billing
            )

            # SEED STAFF
            staff = [
                ("Nurse Asha Sharma", "Nurse", "ICU", "7654321001", "morning"),
                ("Nurse Ravi Kumar", "Nurse", "General Ward", "7654321002", "evening"),
                ("Dr. Support Patel", "Attendant", "General Ward", "7654321003", "night"),
                ("Lab Tech Priya", "Lab Technician", "Laboratory", "7654321004", "morning"),
                ("Admin Rajesh", "Administrator", "Admin", "7654321005", "morning"),
            ]
            cursor.executemany(
                "INSERT INTO staff (name, role, department, phone, shift) VALUES (?, ?, ?, ?, ?)",
                staff
            )

            # SEED MEDICAL RECORDS
            visit_date = datetime.now() - timedelta(days=3)
            medical_records = [
                (1, 1, visit_date, "Hypertension", "Amlodipine 5mg daily, Lisinopril 10mg", "BP reading: 140/90"),
                (2, 2, visit_date + timedelta(days=1), "Migraine", "Sumatriptan 50mg as needed", "Triggered by stress"),
                (3, 3, visit_date - timedelta(days=3), "Fracture Recovery", "Physiotherapy 3x weekly", "Good progress"),
            ]
            cursor.executemany(
                "INSERT INTO medical_records (patient_id, doctor_id, visit_date, diagnosis, prescription, notes) VALUES (?, ?, ?, ?, ?, ?)",
                medical_records
            )

            conn.commit()
            print("✓ Seed data inserted successfully")

    def seed_drug_data(self) -> None:
        """Populate drug interactions and billing codes tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            # Check if drug data already exists
            cursor.execute("SELECT COUNT(*) FROM drug_interactions")
            if cursor.fetchone()[0] > 0:
                print("✓ Drug interaction data already exists. Skipping seed...")
                return

            # SEED DRUG INTERACTIONS
            drug_interactions = [
                ("Aspirin", "Metoprolol", "warning", "May increase bleeding risk"),
                ("Warfarin", "Aspirin", "alert", "Significantly increases bleeding risk"),
                ("Lisinopril", "Potassium", "alert", "May cause hyperkalemia"),
                ("Metformin", "Contrast Dye", "critical", "Risk of acute kidney injury"),
                ("Simvastatin", "Erythromycin", "warning", "Increased statin levels"),
                ("Digoxin", "Verapamil", "alert", "May cause bradycardia and AV block"),
                ("ACE Inhibitor", "NSAIDs", "warning", "Reduced kidney function"),
                ("Methotrexate", "NSAIDs", "warning", "Increased methotrexate toxicity"),
                ("Clopidogrel", "Omeprazole", "warning", "Reduced clopidogrel effectiveness"),
                ("Tramadol", "SSRI", "alert", "Risk of serotonin syndrome"),
                ("Lithium", "NSAIDs", "alert", "Increased lithium levels"),
                ("Phenytoin", "Oral Contraceptives", "warning", "Reduced contraceptive effectiveness"),
                ("Theophylline", "Ciprofloxacin", "warning", "Increased theophylline levels"),
                ("Cyclosporine", "NSAIDs", "alert", "Reduced kidney function"),
                ("Tacrolimus", "Potassium", "warning", "Risk of hyperkalemia"),
            ]
            cursor.executemany(
                "INSERT INTO drug_interactions (drug1, drug2, severity, description) VALUES (?, ?, ?, ?)",
                drug_interactions
            )

            # Check if billing codes exist
            cursor.execute("SELECT COUNT(*) FROM billing_codes")
            if cursor.fetchone()[0] > 0:
                conn.commit()
                print("✓ Billing codes already exist. Skipping seed...")
                return

            # SEED BILLING CODES (ICD-10 and CPT))
            billing_codes = [
                # ICD-10 Diagnosis Codes
                ("I24.0", "ICD-10", "Acute transmural myocardial infarction of anterior wall", "1500.00", "Cardiology"),
                ("I10", "ICD-10", "Essential (primary) hypertension", "150.00", "Cardiology"),
                ("E11.9", "ICD-10", "Type 2 diabetes mellitus without complications", "200.00", "Endocrinology"),
                ("G89.29", "ICD-10", "Chronic pain, unspecified site", "100.00", "Pain Management"),
                ("F41.1", "ICD-10", "Generalized anxiety disorder", "120.00", "Psychiatry"),
                ("M79.3", "ICD-10", "Panniculitis, unspecified", "180.00", "Rheumatology"),
                ("J06.9", "ICD-10", "Acute upper respiratory infection, unspecified", "80.00", "ENT"),
                ("K21.9", "ICD-10", "Unspecified GERD", "90.00", "Gastroenterology"),
                ("M54.5", "ICD-10", "Low back pain", "110.00", "Orthopedics"),
                ("H66.001", "ICD-10", "Acute suppurative otitis media without spontaneous rupture of ear drum, right ear", "140.00", "ENT"),

                # CPT Procedure Codes
                ("99213", "CPT", "Office visit, established patient, moderate complexity", "120.00", "General Practice"),
                ("99214", "CPT", "Office visit, established patient, high complexity", "200.00", "General Practice"),
                ("99215", "CPT", "Office visit, established patient, very high complexity", "300.00", "Specialist"),
                ("99204", "CPT", "Office visit, new patient, moderate to high complexity", "250.00", "General Practice"),
                ("90834", "CPT", "Psychotherapy - 45 minutes", "150.00", "Psychiatry"),
                ("70450", "CPT", "CT head/brain without contrast", "800.00", "Radiology"),
                ("71046", "CPT", "Chest X-ray, 2 views", "120.00", "Radiology"),
                ("76700", "CPT", "Abdominal ultrasound", "250.00", "Radiology"),
                ("85025", "CPT", "Complete blood count with differential", "50.00", "Laboratory"),
                ("80053", "CPT", "Comprehensive metabolic panel", "75.00", "Laboratory"),
            ]
            cursor.executemany(
                "INSERT INTO billing_codes (code, code_type, description, standard_amount, category) VALUES (?, ?, ?, ?, ?)",
                billing_codes
            )

            conn.commit()
            print("✓ Drug interaction and billing code data inserted successfully")

    def reset_database(self) -> None:
        """Drop all tables and recreate schema (useful for testing)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Drop all tables
            tables = [
                'medical_records', 'billing', 'admissions', 'appointments',
                'staff', 'wards', 'doctors', 'patients'
            ]
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

            cursor.execute("PRAGMA foreign_keys = ON")
            conn.commit()
            print("✓ Database reset complete")

    def get_db_stats(self) -> dict:
        """Get basic statistics about the database."""
        stats = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM patients")
            stats['patients'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM doctors")
            stats['doctors'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments")
            stats['appointments'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM admissions WHERE status='admitted'")
            stats['active_admissions'] = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(available_beds) FROM wards")
            result = cursor.fetchone()[0]
            stats['available_beds'] = result if result else 0

            cursor.execute("SELECT SUM(paid_amount) FROM billing WHERE payment_status='pending'")
            result = cursor.fetchone()[0]
            stats['pending_bills'] = result if result else 0

        return stats


def main():
    """Initialize the database with schema and seed data."""
    # Use current directory for database file
    db_manager = DatabaseManager("hms_database.db")

    # Create tables
    db_manager.create_tables()

    # Seed sample data
    db_manager.seed_data()

    # Seed drug data for Ambient AI Scribe
    db_manager.seed_drug_data()

    # Display statistics
    stats = db_manager.get_db_stats()
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"\n✓ Database initialized: {db_manager.db_path}")


if __name__ == "__main__":
    main()
