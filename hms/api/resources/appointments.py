"""Appointment management resources."""

from flask_restful import Resource
from flask import request
from datetime import datetime, date as date_class, timedelta
from hms.api.database import APIDatabase
from hms.api.config import ACTIVE_CONFIG, DB_PATH, VALID_TIME_SLOTS
from hms.api.utils.response import success_response, error_response, validation_error_response, paginated_response
from hms.api.utils.validators import (
    validate_required_fields, validate_date, validate_time_slot,
    validate_date_not_past, validate_appointment_status, validate_pagination_params
)
from hms.api.utils.auth_helper import token_required, role_required


db = APIDatabase(str(DB_PATH))


class AppointmentListResource(Resource):
    """GET /api/appointments - List appointments
    POST /api/appointments - Book new appointment"""

    @token_required
    @role_required("admin", "doctor")
    def get(self):
        """Get all appointments with filters.

        Query params:
            ?date=2025-12-01&status=scheduled&doctor_id=3&page=1&limit=10
        """
        date_filter = request.args.get("date", "")
        status = request.args.get("status", "")
        doctor_id = request.args.get("doctor_id", "")
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)

        is_valid, error_msg = validate_pagination_params(page, limit)
        if not is_valid:
            return error_response(error_msg, code=400), 400

        offset = (page - 1) * limit

        query = """SELECT a.*, p.name as patient_name, d.name as doctor_name
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   JOIN doctors d ON a.doctor_id = d.doctor_id
                   WHERE 1=1"""
        params = []

        if date_filter:
            query += " AND DATE(a.appointment_date) = ?"
            params.append(date_filter)

        if status:
            query += " AND a.status = ?"
            params.append(status)

        if doctor_id:
            query += " AND a.doctor_id = ?"
            params.append(doctor_id)

        count_query = query.replace("SELECT a.*", "SELECT COUNT(*)")
        total = db.count(count_query, tuple(params))

        query += f" ORDER BY a.appointment_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        appointments = db.execute_all(query, tuple(params))

        return paginated_response(
            data=appointments,
            message="Appointments retrieved successfully",
            page=page,
            page_size=limit,
            total=total,
            code=200
        ), 200

    def post(self):
        """Book new appointment.

        Request body:
        {
            "patient_id": 1,
            "doctor_id": 2,
            "appointment_date": "2025-12-01",
            "time_slot": "10:00"
        }
        """
        data = request.get_json() or {}

        required_fields = ["patient_id", "doctor_id", "appointment_date", "time_slot"]
        missing = validate_required_fields(data, required_fields)
        if missing:
            return validation_error_response(missing), 400

        errors = {}

        if not validate_date(data["appointment_date"]):
            errors["appointment_date"] = "Invalid date format (YYYY-MM-DD)"
        elif not validate_date_not_past(data["appointment_date"]):
            errors["appointment_date"] = "Cannot book past dates"

        if not validate_time_slot(data["time_slot"]):
            errors["time_slot"] = f"Must be one of {VALID_TIME_SLOTS}"

        if errors:
            return validation_error_response(errors), 400

        # Verify patient exists
        patient = db.execute_one("SELECT patient_id FROM patients WHERE patient_id = ?", (data["patient_id"],))
        if not patient:
            return error_response("Patient not found", code=404), 404

        # Verify doctor exists
        doctor = db.execute_one("SELECT doctor_id FROM doctors WHERE doctor_id = ?", (data["doctor_id"],))
        if not doctor:
            return error_response("Doctor not found", code=404), 404

        # Check for time slot conflict
        conflict = db.execute_one(
            """SELECT appointment_id FROM appointments
               WHERE doctor_id = ? AND DATE(appointment_date) = ? AND time_slot = ? AND status != 'cancelled'""",
            (data["doctor_id"], data["appointment_date"], data["time_slot"])
        )

        if conflict:
            return error_response(
                "Time slot already booked",
                code=409,
                errors={"time_slot": "Not available"}
            ), 409

        appointment_id = db.execute(
            """INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status)
               VALUES (?, ?, ?, ?, 'scheduled')""",
            (data["patient_id"], data["doctor_id"], data["appointment_date"], data["time_slot"])
        )

        if appointment_id:
            appt = db.execute_one("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))
            return success_response(
                data=appt,
                message="Appointment booked successfully",
                code=201
            ), 201

        return error_response("Failed to book appointment", code=500), 500


class AppointmentResource(Resource):
    """GET /api/appointments/<id> - Get appointment
    PUT /api/appointments/<id> - Reschedule appointment
    PATCH /api/appointments/<id> - Update status
    DELETE /api/appointments/<id> - Cancel appointment"""

    def get(self, appointment_id: int):
        """Get single appointment."""
        appt = db.execute_one(
            """SELECT a.*, p.name as patient_name, d.name as doctor_name
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               JOIN doctors d ON a.doctor_id = d.doctor_id
               WHERE a.appointment_id = ?""",
            (appointment_id,)
        )

        if not appt:
            return error_response("Appointment not found", code=404), 404

        return success_response(
            data=appt,
            message="Appointment retrieved successfully",
            code=200
        ), 200

    @token_required
    def put(self, appointment_id: int):
        """Reschedule appointment."""
        appt = db.execute_one("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))

        if not appt:
            return error_response("Appointment not found", code=404), 404

        if appt["status"] in ["completed", "cancelled"]:
            return error_response(
                f"Cannot reschedule {appt['status']} appointments",
                code=400
            ), 400

        data = request.get_json() or {}

        required_fields = ["appointment_date", "time_slot"]
        missing = validate_required_fields(data, required_fields)
        if missing:
            return validation_error_response(missing), 400

        errors = {}
        if not validate_date(data["appointment_date"]):
            errors["appointment_date"] = "Invalid date format"
        elif not validate_date_not_past(data["appointment_date"]):
            errors["appointment_date"] = "Cannot book past dates"

        if not validate_time_slot(data["time_slot"]):
            errors["time_slot"] = "Invalid time slot"

        if errors:
            return validation_error_response(errors), 400

        # Check for conflicts
        conflict = db.execute_one(
            """SELECT appointment_id FROM appointments
               WHERE doctor_id = ? AND DATE(appointment_date) = ? AND time_slot = ?
               AND appointment_id != ? AND status != 'cancelled'""",
            (appt["doctor_id"], data["appointment_date"], data["time_slot"], appointment_id)
        )

        if conflict:
            return error_response("Time slot unavailable", code=409), 409

        db.execute(
            "UPDATE appointments SET appointment_date = ?, time_slot = ? WHERE appointment_id = ?",
            (data["appointment_date"], data["time_slot"], appointment_id)
        )

        updated = db.execute_one("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))
        return success_response(
            data=updated,
            message="Appointment rescheduled successfully",
            code=200
        ), 200

    @token_required
    def patch(self, appointment_id: int):
        """Update appointment status."""
        appt = db.execute_one("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))

        if not appt:
            return error_response("Appointment not found", code=404), 404

        data = request.get_json() or {}

        if "status" not in data:
            return validation_error_response({"status": "Status is required"}), 400

        if not validate_appointment_status(data["status"]):
            return validation_error_response(
                {"status": "Must be scheduled, completed, or cancelled"}
            ), 400

        new_status = data["status"]

        if new_status == "completed" and "notes" not in data:
            return validation_error_response({"notes": "Notes required for completed appointments"}), 400

        update_data = {"status": new_status}
        if "notes" in data:
            update_data["notes"] = data["notes"]

        set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [appointment_id]
        db.execute(f"UPDATE appointments SET {set_clause} WHERE appointment_id = ?", tuple(values))

        updated = db.execute_one("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))
        return success_response(
            data=updated,
            message="Appointment updated successfully",
            code=200
        ), 200

    @token_required
    def delete(self, appointment_id: int):
        """Cancel appointment."""
        appt = db.execute_one("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,))

        if not appt:
            return error_response("Appointment not found", code=404), 404

        if appt["status"] == "completed":
            return error_response("Cannot cancel completed appointments", code=400), 400

        db.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE appointment_id = ?",
            (appointment_id,)
        )

        return success_response(
            data=None,
            message="Appointment cancelled successfully",
            code=200
        ), 200


class AppointmentAvailableSlotsResource(Resource):
    """GET /api/appointments/available-slots"""

    def get(self):
        """Get available time slots for a doctor on a date.

        Query params:
            ?doctor_id=3&date=2025-12-01
        """
        doctor_id = request.args.get("doctor_id")
        date_str = request.args.get("date")

        if not doctor_id or not date_str:
            return validation_error_response({
                "doctor_id": "Required",
                "date": "Required"
            }), 400

        if not validate_date(date_str):
            return validation_error_response({"date": "Invalid date format"}), 400

        # Check doctor exists
        doctor = db.execute_one("SELECT * FROM doctors WHERE doctor_id = ?", (doctor_id,))
        if not doctor:
            return error_response("Doctor not found", code=404), 404

        # Get booked slots
        booked = db.execute_all(
            """SELECT time_slot FROM appointments
               WHERE doctor_id = ? AND DATE(appointment_date) = ? AND status != 'cancelled'""",
            (doctor_id, date_str)
        )

        booked_slots = {row["time_slot"] for row in booked}

        available_slots = [slot for slot in VALID_TIME_SLOTS if slot not in booked_slots]

        return success_response(
            data={
                "doctor_id": doctor_id,
                "date": date_str,
                "available_slots": available_slots,
                "total_available": len(available_slots)
            },
            message="Available slots retrieved successfully",
            code=200
        ), 200


class AppointmentTodayResource(Resource):
    """GET /api/appointments/today"""

    @token_required
    @role_required("admin", "doctor")
    def get(self):
        """Get all appointments scheduled for today."""
        today = date_class.today().isoformat()

        appointments = db.execute_all(
            """SELECT a.*, p.name as patient_name, d.name as doctor_name
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               JOIN doctors d ON a.doctor_id = d.doctor_id
               WHERE DATE(a.appointment_date) = ? AND a.status = 'scheduled'
               ORDER BY d.doctor_id, a.time_slot""",
            (today,)
        )

        # Group by doctor
        by_doctor = {}
        for appt in appointments:
            doctor_name = appt["doctor_name"]
            if doctor_name not in by_doctor:
                by_doctor[doctor_name] = []
            by_doctor[doctor_name].append(appt)

        return success_response(
            data={"by_doctor": by_doctor, "total": len(appointments)},
            message="Today's appointments retrieved successfully",
            code=200
        ), 200
