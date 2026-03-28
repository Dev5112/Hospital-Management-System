"""
Chart data aggregation queries for HMS visualization layer.
All queries are parameterized to prevent SQL injection.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from hms.api.database import APIDatabase


class AdminChartQueries:
    """Admin dashboard chart queries."""

    @staticmethod
    def get_overview_stats(db: APIDatabase) -> Dict[str, Any]:
        """Get admin overview KPI statistics."""
        stats = {}

        # Total doctors
        result = db.execute_all("SELECT COUNT(*) as count FROM doctors", ())
        stats['total_doctors'] = result[0]['count'] if result else 0

        # Total patients
        result = db.execute_all("SELECT COUNT(*) as count FROM patients", ())
        stats['total_patients'] = result[0]['count'] if result else 0

        # Today's appointments
        today = datetime.now().date().isoformat()
        result = db.execute_all(
            "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = ?",
            (today,)
        )
        stats['todays_appointments'] = result[0]['count'] if result else 0

        # Total revenue (sum of all paid billing amounts)
        result = db.execute_all("SELECT SUM(paid_amount) as total FROM billing", ())
        stats['total_revenue'] = float(result[0]['total']) if result and result[0]['total'] else 0

        # Active admissions
        result = db.execute_all(
            "SELECT COUNT(*) as count FROM admissions WHERE status = ?",
            ('admitted',)
        )
        stats['active_admissions'] = result[0]['count'] if result else 0

        # Available beds
        result = db.execute_all("SELECT SUM(available_beds) as total FROM wards", ())
        stats['available_beds'] = result[0]['total'] if result and result[0]['total'] else 0

        return stats

    @staticmethod
    def get_appointments_trend(db: APIDatabase, days: int = 30) -> List[Dict[str, Any]]:
        """Get appointment count by date for last N days."""
        query = """
        SELECT
            DATE(appointment_date) as date,
            COUNT(*) as count
        FROM appointments
        WHERE appointment_date >= DATE('now', ? || ' days')
        GROUP BY DATE(appointment_date)
        ORDER BY appointment_date ASC
        """
        return db.execute_all(query, (f'-{days}',))

    @staticmethod
    def get_appointments_by_status(db: APIDatabase) -> List[Dict[str, Any]]:
        """Get appointment count by status."""
        query = """
        SELECT
            status,
            COUNT(*) as count
        FROM appointments
        GROUP BY status
        ORDER BY count DESC
        """
        return db.execute_all(query, ())

    @staticmethod
    def get_top_specializations(db: APIDatabase, limit: int = 8) -> List[Dict[str, Any]]:
        """Get top specializations by appointment count."""
        query = """
        SELECT
            d.specialization,
            COUNT(a.appointment_id) as count
        FROM doctors d
        LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
        GROUP BY d.specialization
        ORDER BY count DESC
        LIMIT ?
        """
        return db.execute_all(query, (limit,))

    @staticmethod
    def get_revenue_by_month(db: APIDatabase, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get monthly revenue for the year."""
        if year is None:
            year = datetime.now().year

        query = """
        SELECT
            CAST(strftime('%m', b.payment_date) AS INTEGER) as month,
            SUM(b.paid_amount) as total_amount
        FROM billing b
        WHERE strftime('%Y', b.payment_date) = ?
        GROUP BY strftime('%m', b.payment_date)
        ORDER BY month ASC
        """
        return db.execute_all(query, (str(year),))

    @staticmethod
    def get_bed_occupancy_by_ward(db: APIDatabase) -> List[Dict[str, Any]]:
        """Get bed occupancy percentage by ward type."""
        query = """
        SELECT
            ward_type,
            ROUND((SUM(total_beds - available_beds) * 100.0) / SUM(total_beds), 2) as occupancy_percent
        FROM wards
        GROUP BY ward_type
        ORDER BY ward_type ASC
        """
        return db.execute_all(query, ())

    @staticmethod
    def get_patient_gender_split(db: APIDatabase) -> List[Dict[str, Any]]:
        """Get patient count by gender."""
        query = """
        SELECT
            gender,
            COUNT(*) as count
        FROM patients
        GROUP BY gender
        ORDER BY count DESC
        """
        return db.execute_all(query, ())

    @staticmethod
    def get_admissions_vs_discharges(db: APIDatabase, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily admissions vs discharges for last N days."""
        query = """
        SELECT
            DATE(admission_date) as date,
            SUM(CASE WHEN 1=1 THEN 1 ELSE 0 END) as admissions,
            SUM(CASE WHEN discharge_date IS NOT NULL THEN 1 ELSE 0 END) as discharges
        FROM admissions
        WHERE admission_date >= DATE('now', ? || ' days')
        GROUP BY DATE(admission_date)
        ORDER BY admission_date ASC
        """
        return db.execute_all(query, (f'-{days}',))

    @staticmethod
    def get_top_diagnoses(db: APIDatabase, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top diagnoses by count."""
        query = """
        SELECT
            diagnosis,
            COUNT(*) as count
        FROM medical_records
        WHERE diagnosis IS NOT NULL AND diagnosis != ''
        GROUP BY diagnosis
        ORDER BY count DESC
        LIMIT ?
        """
        return db.execute_all(query, (limit,))


class DoctorChartQueries:
    """Doctor dashboard chart queries."""

    @staticmethod
    def get_doctor_appointment_distribution(db: APIDatabase, doctor_id: int) -> List[Dict[str, Any]]:
        """Get appointments by day of week for a doctor."""
        query = """
        SELECT
            CASE CAST(strftime('%w', appointment_date) AS INTEGER)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as day_of_week,
            COUNT(*) as count
        FROM appointments
        WHERE doctor_id = ?
        GROUP BY strftime('%w', appointment_date)
        ORDER BY CAST(strftime('%w', appointment_date) AS INTEGER) ASC
        """
        return db.execute_all(query, (doctor_id,))

    @staticmethod
    def get_doctor_status_breakdown(db: APIDatabase, doctor_id: int) -> List[Dict[str, Any]]:
        """Get appointment status breakdown for a doctor."""
        query = """
        SELECT
            status,
            COUNT(*) as count
        FROM appointments
        WHERE doctor_id = ?
        GROUP BY status
        ORDER BY count DESC
        """
        return db.execute_all(query, (doctor_id,))

    @staticmethod
    def get_doctor_weekly_heatmap(db: APIDatabase, doctor_id: int) -> Dict[str, Any]:
        """Get doctor's schedule heatmap for this week."""
        # Define time slots (30-min intervals from 09:00 to 17:30)
        hours = []
        for h in range(9, 18):
            for m in [0, 30]:
                hours.append(f"{h:02d}:{m:02d}")

        # Define days
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Get all appointments for this doctor this week
        query = """
        SELECT
            DATE(appointment_date) as date,
            time_slot,
            patient_id
        FROM appointments
        WHERE doctor_id = ?
        AND appointment_date >= DATE('now', 'weekday 1', '-7 days')
        AND appointment_date <= DATE('now', 'weekday 1', '-7 days', '+6 days')
        ORDER BY appointment_date, time_slot
        """
        appointments = db.execute_all(query, (doctor_id,))

        # Build data matrix
        data = [[0 for _ in hours] for _ in days]
        patient_map = [[None for _ in hours] for _ in days]

        for apt in appointments:
            try:
                apt_date = apt['date']
                time_slot = apt['time_slot']
                patient_id = apt['patient_id']

                # Convert date to day index (0=Monday, 6=Sunday)
                apt_datetime = datetime.fromisoformat(apt_date)
                day_index = apt_datetime.weekday()

                # Convert time slot to hour index
                time_parts = time_slot.replace("AM", "").replace("PM", "").strip().split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                # Find matching hour slot
                slot_time = f"{hour:02d}:{minute:02d}"
                if slot_time in hours:
                    hour_index = hours.index(slot_time)
                    data[day_index][hour_index] = 1
                    patient_map[day_index][hour_index] = patient_id
            except Exception:
                pass

        return {
            "days": days,
            "hours": hours,
            "data": data,
            "patients": patient_map
        }

    @staticmethod
    def get_doctor_top_diagnoses(db: APIDatabase, doctor_id: int) -> List[Dict[str, Any]]:
        """Get top diagnoses given by a doctor."""
        query = """
        SELECT
            diagnosis,
            COUNT(*) as count
        FROM medical_records
        WHERE doctor_id = ? AND diagnosis IS NOT NULL AND diagnosis != ''
        GROUP BY diagnosis
        ORDER BY count DESC
        LIMIT 5
        """
        return db.execute_all(query, (doctor_id,))

    @staticmethod
    def get_doctor_monthly_patients(db: APIDatabase, doctor_id: int) -> List[Dict[str, Any]]:
        """Get patient count per month this year for a doctor."""
        query = """
        SELECT
            CAST(strftime('%m', a.appointment_date) AS INTEGER) as month,
            COUNT(DISTINCT a.patient_id) as count
        FROM appointments a
        WHERE a.doctor_id = ?
        AND strftime('%Y', a.appointment_date) = ?
        GROUP BY strftime('%m', a.appointment_date)
        ORDER BY month ASC
        """
        current_year = str(datetime.now().year)
        return db.execute_all(query, (doctor_id, current_year))


class PatientChartQueries:
    """Patient dashboard chart queries."""

    @staticmethod
    def get_patient_treatment_timeline(db: APIDatabase, patient_id: int) -> List[Dict[str, Any]]:
        """Get treatment history timeline for a patient."""
        timeline = []

        # Get appointments
        apt_query = """
        SELECT
            DATE(a.appointment_date) as date,
            'appointment' as type,
            d.name as doctor,
            d.specialization as specialization,
            a.status,
            a.notes as description
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
        """
        appointments = db.execute_all(apt_query, (patient_id,))
        for apt in appointments:
            timeline.append({
                'date': apt['date'],
                'type': 'appointment',
                'description': apt['specialization'] or 'Appointment',
                'doctor': apt['doctor'],
                'status': apt['status']
            })

        # Get admissions
        adm_query = """
        SELECT
            DATE(a.admission_date) as date,
            'admission' as type,
            w.ward_name,
            a.diagnosis,
            CASE
                WHEN a.discharge_date IS NOT NULL
                THEN CAST((julianday(a.discharge_date) - julianday(a.admission_date)) AS INTEGER)
                ELSE NULL
            END as duration_days,
            a.status
        FROM admissions a
        JOIN wards w ON a.ward_id = w.ward_id
        WHERE a.patient_id = ?
        ORDER BY a.admission_date DESC
        """
        admissions = db.execute_all(adm_query, (patient_id,))
        for adm in admissions:
            timeline.append({
                'date': adm['date'],
                'type': 'admission',
                'description': adm['diagnosis'] or 'Hospital Admission',
                'ward': adm['ward_name'],
                'duration_days': adm['duration_days'],
                'status': adm['status']
            })

        # Sort by date descending
        timeline.sort(key=lambda x: x['date'], reverse=True)
        return timeline

    @staticmethod
    def get_patient_billing_history(db: APIDatabase, patient_id: int) -> List[Dict[str, Any]]:
        """Get billing history for a patient."""
        query = """
        SELECT
            strftime('%Y-%m', b.payment_date) as month,
            SUM(b.total_amount) as total_billed,
            SUM(b.paid_amount) as amount_paid
        FROM billing b
        WHERE b.patient_id = ?
        GROUP BY strftime('%Y-%m', b.payment_date)
        ORDER BY month DESC
        """
        return db.execute_all(query, (patient_id,))

    @staticmethod
    def get_patient_visit_frequency(db: APIDatabase, patient_id: int) -> List[Dict[str, Any]]:
        """Get visit frequency (appointments) per month for last 12 months."""
        query = """
        SELECT
            strftime('%Y-%m', a.appointment_date) as month,
            COUNT(*) as count
        FROM appointments a
        WHERE a.patient_id = ?
        AND a.appointment_date >= DATE('now', '-12 months')
        GROUP BY strftime('%Y-%m', a.appointment_date)
        ORDER BY month ASC
        """
        return db.execute_all(query, (patient_id,))

    @staticmethod
    def get_patient_diagnosis_breakdown(db: APIDatabase, patient_id: int) -> List[Dict[str, Any]]:
        """Get all diagnoses received by a patient."""
        query = """
        SELECT
            diagnosis,
            COUNT(*) as count
        FROM medical_records
        WHERE patient_id = ? AND diagnosis IS NOT NULL AND diagnosis != ''
        GROUP BY diagnosis
        ORDER BY count DESC
        """
        return db.execute_all(query, (patient_id,))

    @staticmethod
    def get_patient_outstanding_balance(db: APIDatabase, patient_id: int) -> float:
        """Get outstanding balance for a patient."""
        query = """
        SELECT
            SUM(total_amount - paid_amount) as outstanding
        FROM billing
        WHERE patient_id = ? AND payment_status IN ('pending', 'partial')
        """
        result = db.execute_all(query, (patient_id,))
        return float(result[0]['outstanding']) if result and result[0]['outstanding'] else 0.0

    @staticmethod
    def get_patient_last_visit(db: APIDatabase, patient_id: int) -> Optional[str]:
        """Get last visit date for a patient."""
        query = """
        SELECT MAX(appointment_date) as last_visit
        FROM appointments
        WHERE patient_id = ? AND status = 'completed'
        """
        result = db.execute_all(query, (patient_id,))
        return result[0]['last_visit'] if result and result[0]['last_visit'] else None

    @staticmethod
    def get_patient_total_visits(db: APIDatabase, patient_id: int) -> int:
        """Get total number of visits (completed appointments) for a patient."""
        query = """
        SELECT COUNT(*) as total
        FROM appointments
        WHERE patient_id = ? AND status = 'completed'
        """
        result = db.execute_all(query, (patient_id,))
        return result[0]['total'] if result else 0
