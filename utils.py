"""
Hospital Management System - Utilities & Helpers
Additional utilities for HMS operations and reporting.
"""

from database import DatabaseManager
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
import json


class ReportGenerator:
    """Generate various HMS reports."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager

    def patient_admission_history(self, patient_id: int) -> List[Dict]:
        """Get complete admission history for a patient."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.*, w.ward_name, d.name as doctor_name
                FROM admissions a
                JOIN wards w ON a.ward_id = w.ward_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.patient_id = ?
                ORDER BY a.admission_date DESC
            """
            cursor.execute(query, (patient_id,))
            result = []
            for row in cursor.fetchall():
                result.append(dict(row))
            return result

    def ward_census_report(self) -> Dict:
        """Get detailed ward census report."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT w.ward_id, w.ward_name, w.ward_type, w.total_beds, w.available_beds,
                       COUNT(a.admission_id) as occupied_count,
                       (w.total_beds - w.available_beds) as occupied_beds
                FROM wards w
                LEFT JOIN admissions a ON w.ward_id = a.ward_id AND a.status = 'admitted'
                GROUP BY w.ward_id
                ORDER BY w.ward_type, w.ward_name
            """
            cursor.execute(query)
            result = {}
            for row in cursor.fetchall():
                ward_name = row['ward_name']
                result[ward_name] = {
                    'ward_type': row['ward_type'],
                    'total_beds': row['total_beds'],
                    'occupied_beds': row['occupied_beds'],
                    'available_beds': row['available_beds'],
                    'patients': row['occupied_count'],
                    'occupancy_rate': (row['occupied_beds'] / row['total_beds'] * 100) if row['total_beds'] > 0 else 0
                }
            return result

    def monthly_revenue_report(self, months: int = 6) -> List[Dict]:
        """Generate monthly revenue report."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT strftime('%Y-%m', created_at) as month,
                       COUNT(*) as bill_count,
                       SUM(total_amount) as total_billed,
                       SUM(paid_amount) as total_paid,
                       SUM(total_amount) - SUM(paid_amount) as outstanding
                FROM billing
                WHERE created_at >= datetime('now', ? || ' months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
            """
            cursor.execute(query, (f"-{months}",))
            result = []
            for row in cursor.fetchall():
                result.append(dict(row))
            return result

    def doctor_workload_report(self) -> List[Dict]:
        """Get doctor workload and performance metrics."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT d.doctor_id, d.name, d.specialization, d.phone,
                       COUNT(a.appointment_id) as total_appointments,
                       SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN a.status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                       SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                       COUNT(adm.admission_id) as active_patients
                FROM doctors d
                LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
                LEFT JOIN admissions adm ON d.doctor_id = adm.doctor_id AND adm.status = 'admitted'
                GROUP BY d.doctor_id
                ORDER BY completed DESC
            """
            cursor.execute(query)
            result = []
            for row in cursor.fetchall():
                total = row['total_appointments'] if row['total_appointments'] else 0
                completion_rate = (row['completed'] / total * 100) if total > 0 else 0
                result.append({
                    'doctor_id': row['doctor_id'],
                    'name': row['name'],
                    'specialization': row['specialization'],
                    'phone': row['phone'],
                    'total_appointments': total,
                    'completed_appointments': row['completed'],
                    'scheduled_appointments': row['scheduled'],
                    'cancelled_appointments': row['cancelled'],
                    'active_patients': row['active_patients'],
                    'completion_rate': completion_rate
                })
            return result

    def outstanding_bills_summary(self) -> Dict:
        """Get summary of outstanding bills."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) as total_bills,
                       SUM(total_amount) as total_billed,
                       SUM(paid_amount) as total_paid,
                       SUM(total_amount) - SUM(paid_amount) as outstanding
                FROM billing
                WHERE payment_status IN ('pending', 'partial')
            """
            cursor.execute(query)
            row = cursor.fetchone()

            return {
                'total_bills': row['total_bills'],
                'total_billed': row['total_billed'] or 0,
                'total_paid': row['total_paid'] or 0,
                'outstanding': row['outstanding'] or 0
            }


class ValidationHelper:
    """Validation utilities for HMS data."""

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        return len(phone) >= 10 and phone.replace('-', '').replace('+', '').isdigit()

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        return '@' in email and '.' in email.split('@')[1]

    @staticmethod
    def validate_blood_group(blood_group: str) -> bool:
        """Validate blood group."""
        valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        return blood_group in valid_groups

    @staticmethod
    def validate_gender(gender: str) -> bool:
        """Validate gender."""
        return gender in ['M', 'F', 'Other']

    @staticmethod
    def validate_ward_type(ward_type: str) -> bool:
        """Validate ward type."""
        return ward_type in ['general', 'ICU', 'private']

    @staticmethod
    def validate_appointment_status(status: str) -> bool:
        """Validate appointment status."""
        return status in ['scheduled', 'completed', 'cancelled']

    @staticmethod
    def validate_payment_status(status: str) -> bool:
        """Validate payment status."""
        return status in ['pending', 'partial', 'paid']


class BackupRestore:
    """Database backup and restore utilities."""

    @staticmethod
    def backup_database(db_manager: DatabaseManager, backup_path: str) -> bool:
        """Create backup of database."""
        import shutil
        try:
            shutil.copy2(db_manager.db_path, backup_path)
            print(f"✓ Database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False

    @staticmethod
    def export_data_json(db_manager: DatabaseManager, output_file: str) -> bool:
        """Export all data to JSON format."""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                data = {}

                # Export each table
                tables = ['patients', 'doctors', 'appointments', 'wards', 'admissions', 'billing', 'staff', 'medical_records']
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    data[table] = [dict(row) for row in rows]

                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

                print(f"✓ Data exported to: {output_file}")
                return True
        except Exception as e:
            print(f"✗ Export failed: {e}")
            return False


class DataValidator:
    """Validate referential integrity and data consistency."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager
        self.errors = []

    def validate_foreign_keys(self) -> bool:
        """Validate all foreign key relationships."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check appointments references
            cursor.execute("""
                SELECT COUNT(*) FROM appointments a
                WHERE a.patient_id NOT IN (SELECT patient_id FROM patients)
                OR a.doctor_id NOT IN (SELECT doctor_id FROM doctors)
            """)
            if cursor.fetchone()[0] > 0:
                self.errors.append("Invalid references in appointments table")

            # Check admissions references
            cursor.execute("""
                SELECT COUNT(*) FROM admissions a
                WHERE a.patient_id NOT IN (SELECT patient_id FROM patients)
                OR a.doctor_id NOT IN (SELECT doctor_id FROM doctors)
                OR a.ward_id NOT IN (SELECT ward_id FROM wards)
            """)
            if cursor.fetchone()[0] > 0:
                self.errors.append("Invalid references in admissions table")

            # Check billing references
            cursor.execute("""
                SELECT COUNT(*) FROM billing b
                WHERE b.patient_id NOT IN (SELECT patient_id FROM patients)
            """)
            if cursor.fetchone()[0] > 0:
                self.errors.append("Invalid references in billing table")

        return len(self.errors) == 0

    def validate_data_constraints(self) -> bool:
        """Validate data constraints."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check available_beds don't exceed total_beds
            cursor.execute("""
                SELECT COUNT(*) FROM wards WHERE available_beds > total_beds
            """)
            if cursor.fetchone()[0] > 0:
                self.errors.append("Available beds exceed total beds in some wards")

            # Check paid_amount doesn't exceed total_amount
            cursor.execute("""
                SELECT COUNT(*) FROM billing WHERE paid_amount > total_amount
            """)
            if cursor.fetchone()[0] > 0:
                self.errors.append("Paid amount exceeds total amount in some bills")

        return len(self.errors) == 0

    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors


# Example usage
if __name__ == "__main__":
    db_manager = DatabaseManager("hms_database.db")
    db_manager.create_tables()
    db_manager.seed_data()

    print("\n=== REPORT EXAMPLES ===\n")

    # Generate reports
    report_gen = ReportGenerator(db_manager)

    print("1. Ward Census Report:")
    print("-" * 70)
    census = report_gen.ward_census_report()
    for ward_name, details in census.items():
        print(f"   {ward_name:<20} | Occupancy: {details['occupancy_rate']:6.2f}% | Patients: {details['patients']}")

    print("\n2. Doctor Workload Report:")
    print("-" * 70)
    workload = report_gen.doctor_workload_report()
    for doc in workload[:3]:
        print(f"   Dr. {doc['name']:<20} | Completed: {doc['completion_rate']:6.2f}% | Active Patients: {doc['active_patients']}")

    print("\n3. Outstanding Bills Summary:")
    print("-" * 70)
    bills = report_gen.outstanding_bills_summary()
    print(f"   Total Bills: {bills['total_bills']}")
    print(f"   Outstanding Amount: Rs. {bills['outstanding']:.2f}\n")

    # Export data
    print("\n=== UTILITY EXAMPLES ===\n")
    backup = BackupRestore()
    backup.export_data_json(db_manager, "hms_backup.json")

    # Validate data
    validator = DataValidator(db_manager)
    if validator.validate_foreign_keys() and validator.validate_data_constraints():
        print("✓ All data validations passed!")
    else:
        print("✗ Validation errors found:")
        for error in validator.get_errors():
            print(f"  - {error}")
