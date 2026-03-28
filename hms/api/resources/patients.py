"""Patient management resources."""

from flask_restful import Resource
from flask import request, g
from datetime import datetime
from hms.api.database import APIDatabase
from hms.api.config import ACTIVE_CONFIG, DB_PATH, VALID_BLOOD_GROUPS, VALID_GENDERS
from hms.api.utils.response import success_response, error_response, validation_error_response, paginated_response
from hms.api.utils.validators import (
    validate_phone, validate_required_fields, validate_blood_group,
    validate_gender, validate_date, validate_pagination_params
)
from hms.api.utils.auth_helper import token_required, role_required


db = APIDatabase(str(DB_PATH))


class PatientListResource(Resource):
    """GET /api/patients - List all patients
    POST /api/patients - Register new patient"""

    def get(self):
        """Get all patients with filters.

        Query params:
            ?blood_group=A+&gender=M&page=1&limit=10
        """
        blood_group = request.args.get("blood_group", "")
        gender = request.args.get("gender", "")
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)

        is_valid, error_msg = validate_pagination_params(page, limit)
        if not is_valid:
            return error_response(error_msg, code=400), 400

        offset = (page - 1) * limit

        query = "SELECT * FROM patients WHERE 1=1"
        params = []

        if blood_group:
            query += " AND blood_group = ?"
            params.append(blood_group)

        if gender:
            query += " AND gender = ?"
            params.append(gender)

        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = db.count(count_query, tuple(params))

        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        patients = db.execute_all(query, tuple(params))

        return paginated_response(
            data=patients,
            message="Patients retrieved successfully",
            page=page,
            page_size=limit,
            total=total,
            code=200
        ), 200

    def post(self):
        """Register new patient.

        Request body:
        {
            "name": "John Doe",
            "dob": "1990-05-15",
            "gender": "M",
            "phone": "9876543210",
            "address": "123 Main St",
            "blood_group": "A+"
        }
        """
        data = request.get_json() or {}

        required_fields = ["name", "dob", "gender", "phone", "blood_group"]
        missing = validate_required_fields(data, required_fields)
        if missing:
            return validation_error_response(missing), 400

        errors = {}

        if not validate_date(data["dob"]):
            errors["dob"] = "Invalid date format (YYYY-MM-DD)"

        if not validate_gender(data["gender"]):
            errors["gender"] = f"Must be one of {VALID_GENDERS}"

        if not validate_phone(data["phone"]):
            errors["phone"] = "Must be 10 digits"

        if not validate_blood_group(data["blood_group"]):
            errors["blood_group"] = f"Must be one of {VALID_BLOOD_GROUPS}"

        if errors:
            return validation_error_response(errors), 400

        # Check if phone exists
        existing = db.execute_one("SELECT patient_id FROM patients WHERE phone = ?", (data["phone"],))
        if existing:
            return error_response("Phone number already registered", code=409), 409

        patient_id = db.execute(
            """INSERT INTO patients (name, dob, gender, phone, address, blood_group)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data["name"], data["dob"], data["gender"], data["phone"],
             data.get("address", ""), data["blood_group"])
        )

        if patient_id:
            patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
            return success_response(
                data=patient,
                message="Patient registered successfully",
                code=201
            ), 201

        return error_response("Failed to register patient", code=500), 500


class PatientResource(Resource):
    """GET /api/patients/<id> - Get patient
    PUT /api/patients/<id> - Update patient
    PATCH /api/patients/<id> - Partial update
    DELETE /api/patients/<id> - Deactivate patient"""

    def get(self, patient_id: int):
        """Get patient profile with related data."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))

        if not patient:
            return error_response("Patient not found", code=404), 404

        # Get appointments count
        appointment_count = db.count(
            "SELECT COUNT(*) FROM appointments WHERE patient_id = ? AND status != 'cancelled'",
            (patient_id,)
        )

        # Get last visit date
        last_visit = db.execute_one(
            "SELECT MAX(appointment_date) as last_visit FROM appointments WHERE patient_id = ? AND status = 'completed'",
            (patient_id,)
        )

        # Get active admissions
        active_admissions = db.count(
            "SELECT COUNT(*) FROM admissions WHERE patient_id = ? AND discharge_date IS NULL",
            (patient_id,)
        )

        patient["total_appointments"] = appointment_count
        patient["last_visit"] = last_visit.get("last_visit") if last_visit else None
        patient["active_admissions"] = active_admissions

        return success_response(
            data=patient,
            message="Patient retrieved successfully",
            code=200
        ), 200

    @token_required
    @role_required("admin")
    def put(self, patient_id: int):
        """Full update of patient."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not patient:
            return error_response("Patient not found", code=404), 404

        data = request.get_json() or {}

        required_fields = ["name", "dob", "gender", "phone", "blood_group"]
        missing = validate_required_fields(data, required_fields)
        if missing:
            return validation_error_response(missing), 400

        errors = {}
        if not validate_date(data["dob"]):
            errors["dob"] = "Invalid date format"
        if not validate_gender(data["gender"]):
            errors["gender"] = "Invalid gender"
        if not validate_phone(data["phone"]):
            errors["phone"] = "Must be 10 digits"
        if not validate_blood_group(data["blood_group"]):
            errors["blood_group"] = "Invalid blood group"

        if errors:
            return validation_error_response(errors), 400

        existing = db.execute_one(
            "SELECT patient_id FROM patients WHERE phone = ? AND patient_id != ?",
            (data["phone"], patient_id)
        )
        if existing:
            return error_response("Phone already in use", code=409), 409

        db.execute(
            """UPDATE patients SET name = ?, dob = ?, gender = ?, phone = ?, address = ?, blood_group = ?
               WHERE patient_id = ?""",
            (data["name"], data["dob"], data["gender"], data["phone"],
             data.get("address", ""), data["blood_group"], patient_id)
        )

        updated = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        return success_response(
            data=updated,
            message="Patient updated successfully",
            code=200
        ), 200

    @token_required
    @role_required("admin", "patient")
    def patch(self, patient_id: int):
        """Partial update of patient."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not patient:
            return error_response("Patient not found", code=404), 404

        data = request.get_json() or {}
        updates = {}

        if "phone" in data:
            if not validate_phone(data["phone"]):
                return validation_error_response({"phone": "Must be 10 digits"}), 400
            updates["phone"] = data["phone"]

        if "address" in data:
            updates["address"] = data["address"]

        if "blood_group" in data:
            if not validate_blood_group(data["blood_group"]):
                return validation_error_response({"blood_group": "Invalid blood group"}), 400
            updates["blood_group"] = data["blood_group"]

        if not updates:
            return error_response("No fields to update", code=400), 400

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [patient_id]
        db.execute(f"UPDATE patients SET {set_clause} WHERE patient_id = ?", tuple(values))

        updated = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        return success_response(
            data=updated,
            message="Patient updated successfully",
            code=200
        ), 200

    @token_required
    @role_required("admin")
    def delete(self, patient_id: int):
        """Soft delete patient."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not patient:
            return error_response("Patient not found", code=404), 404

        return success_response(
            data=None,
            message="Patient deactivated successfully",
            code=200
        ), 200


class PatientAppointmentsResource(Resource):
    """GET /api/patients/<id>/appointments"""

    def get(self, patient_id: int):
        """Get patient's appointments."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not patient:
            return error_response("Patient not found", code=404), 404

        status = request.args.get("status", "")

        query = """SELECT a.*, d.name as doctor_name, d.specialization
                   FROM appointments a
                   JOIN doctors d ON a.doctor_id = d.doctor_id
                   WHERE a.patient_id = ?"""
        params = [patient_id]

        if status:
            query += " AND a.status = ?"
            params.append(status)

        query += " ORDER BY a.appointment_date DESC"

        appointments = db.execute_all(query, tuple(params))

        return success_response(
            data=appointments,
            message="Appointments retrieved successfully",
            code=200
        ), 200


class PatientMedicalRecordsResource(Resource):
    """GET /api/patients/<id>/medical-records"""

    def get(self, patient_id: int):
        """Get patient's medical records."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not patient:
            return error_response("Patient not found", code=404), 404

        records = db.execute_all(
            """SELECT mr.*, d.name as doctor_name
               FROM medical_records mr
               LEFT JOIN doctors d ON mr.doctor_id = d.doctor_id
               WHERE mr.patient_id = ?
               ORDER BY mr.visit_date DESC""",
            (patient_id,)
        )

        return success_response(
            data=records,
            message="Medical records retrieved successfully",
            code=200
        ), 200


class PatientBillingResource(Resource):
    """GET /api/patients/<id>/billing"""

    def get(self, patient_id: int):
        """Get patient's bills."""
        patient = db.execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not patient:
            return error_response("Patient not found", code=404), 404

        status = request.args.get("status", "")

        query = "SELECT * FROM billing WHERE patient_id = ?"
        params = [patient_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY billing_date DESC"

        bills = db.execute_all(query, tuple(params))

        return success_response(
            data=bills,
            message="Billing records retrieved successfully",
            code=200
        ), 200
