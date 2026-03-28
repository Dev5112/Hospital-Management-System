"""Ward management resources."""

from flask_restful import Resource
from flask import request
from hms.api.database import APIDatabase
from hms.api.config import ACTIVE_CONFIG, DB_PATH, VALID_WARD_TYPES
from hms.api.utils.response import success_response, error_response, validation_error_response, paginated_response
from hms.api.utils.validators import (
    validate_required_fields, validate_positive_number, validate_pagination_params
)
from hms.api.utils.auth_helper import token_required, role_required


db = APIDatabase(str(DB_PATH))


class WardListResource(Resource):
    """GET /api/wards - List wards
    POST /api/wards - Create new ward"""

    def get(self):
        """Get all wards with occupancy info.

        Query params:
            ?type=ICU&page=1&limit=10
        """
        ward_type = request.args.get("type", "")
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)

        is_valid, error_msg = validate_pagination_params(page, limit)
        if not is_valid:
            return error_response(error_msg, code=400), 400

        offset = (page - 1) * limit

        query = "SELECT * FROM wards WHERE 1=1"
        params = []

        if ward_type:
            query += " AND ward_type = ?"
            params.append(ward_type)

        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = db.count(count_query, tuple(params))

        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        wards = db.execute_all(query, tuple(params))

        # Add occupancy info
        for ward in wards:
            ward["available_beds"] = ward.get("available_beds", 0)
            ward["occupied_beds"] = ward["total_beds"] - ward["available_beds"]
            ward["occupancy_percentage"] = (ward["occupied_beds"] / ward["total_beds"] * 100) if ward["total_beds"] > 0 else 0

        return paginated_response(
            data=wards,
            message="Wards retrieved successfully",
            page=page,
            page_size=limit,
            total=total,
            code=200
        ), 200

    @token_required
    @role_required("admin")
    def post(self):
        """Create new ward.

        Request body:
        {
            "name": "ICU Ward A",
            "ward_type": "ICU",
            "total_beds": 20,
            "available_beds": 20
        }
        """
        data = request.get_json() or {}

        required_fields = ["name", "ward_type", "total_beds"]
        missing = validate_required_fields(data, required_fields)
        if missing:
            return validation_error_response(missing), 400

        errors = {}

        if not validate_positive_number(data["total_beds"]):
            errors["total_beds"] = "Must be a positive number"

        if data["ward_type"] not in VALID_WARD_TYPES:
            errors["ward_type"] = f"Must be one of {VALID_WARD_TYPES}"

        if errors:
            return validation_error_response(errors), 400

        available_beds = data.get("available_beds", data["total_beds"])

        if available_beds > data["total_beds"]:
            return error_response(
                "Available beds cannot exceed total beds",
                code=400
            ), 400

        ward_id = db.execute(
            """INSERT INTO wards (name, ward_type, total_beds, available_beds)
               VALUES (?, ?, ?, ?)""",
            (data["name"], data["ward_type"], int(data["total_beds"]), int(available_beds))
        )

        if ward_id:
            ward = db.execute_one("SELECT * FROM wards WHERE ward_id = ?", (ward_id,))
            ward["occupied_beds"] = ward["total_beds"] - ward["available_beds"]
            ward["occupancy_percentage"] = (ward["occupied_beds"] / ward["total_beds"] * 100)
            return success_response(
                data=ward,
                message="Ward created successfully",
                code=201
            ), 201

        return error_response("Failed to create ward", code=500), 500


class WardResource(Resource):
    """GET /api/wards/<id> - Get ward"""

    def get(self, ward_id: int):
        """Get single ward with current patients."""
        ward = db.execute_one("SELECT * FROM wards WHERE ward_id = ?", (ward_id,))

        if not ward:
            return error_response("Ward not found", code=404), 404

        # Get current patients in this ward
        patients = db.execute_all(
            """SELECT p.*, a.admission_id, a.admission_date
               FROM patients p
               JOIN admissions a ON p.patient_id = a.patient_id
               WHERE a.ward_id = ? AND a.discharge_date IS NULL""",
            (ward_id,)
        )

        ward["occupied_beds"] = ward["total_beds"] - ward["available_beds"]
        ward["occupancy_percentage"] = (ward["occupied_beds"] / ward["total_beds"] * 100) if ward["total_beds"] > 0 else 0
        ward["current_patients"] = patients

        return success_response(
            data=ward,
            message="Ward retrieved successfully",
            code=200
        ), 200


class WardBedsResource(Resource):
    """PATCH /api/wards/<id>/beds - Update bed availability"""

    @token_required
    @role_required("admin")
    def patch(self, ward_id: int):
        """Update available beds.

        Request body:
        {
            "action": "admit" | "discharge",
            "count": 1
        }
        """
        ward = db.execute_one("SELECT * FROM wards WHERE ward_id = ?", (ward_id,))

        if not ward:
            return error_response("Ward not found", code=404), 404

        data = request.get_json() or {}

        if "action" not in data:
            return validation_error_response({"action": "Action is required (admit or discharge)"}), 400

        action = data["action"].lower()
        count = data.get("count", 1)

        if action not in ["admit", "discharge"]:
            return validation_error_response({"action": "Must be 'admit' or 'discharge'"}), 400

        if not validate_positive_number(count) or int(count) < 1:
            return validation_error_response({"count": "Must be a positive integer"}), 400

        count = int(count)
        current_available = ward["available_beds"]

        if action == "admit":
            if current_available < count:
                return error_response(
                    f"Not enough beds available. Available: {current_available}, Requested: {count}",
                    code=400
                ), 400
            new_available = current_available - count
        else:  # discharge
            if current_available + count > ward["total_beds"]:
                return error_response(
                    f"Cannot discharge {count} beds. Max capacity: {ward['total_beds']}",
                    code=400
                ), 400
            new_available = current_available + count

        db.execute(
            "UPDATE wards SET available_beds = ? WHERE ward_id = ?",
            (new_available, ward_id)
        )

        updated = db.execute_one("SELECT * FROM wards WHERE ward_id = ?", (ward_id,))
        updated["occupied_beds"] = updated["total_beds"] - updated["available_beds"]
        updated["occupancy_percentage"] = (updated["occupied_beds"] / updated["total_beds"] * 100)

        return success_response(
            data=updated,
            message=f"Bed {action}ed successfully",
            code=200
        ), 200


class WardOccupancyResource(Resource):
    """GET /api/wards/occupancy - Ward occupancy statistics"""

    @token_required
    @role_required("admin")
    def get(self):
        """Get occupancy percentage for all wards."""
        wards = db.execute_all(
            """SELECT ward_id, name, ward_type, total_beds, available_beds
               FROM wards
               ORDER BY ward_type, name"""
        )

        occupancy_data = []
        for ward in wards:
            occupied = ward["total_beds"] - ward["available_beds"]
            occupancy_pct = (occupied / ward["total_beds"] * 100) if ward["total_beds"] > 0 else 0

            occupancy_data.append({
                "ward_id": ward["ward_id"],
                "ward": ward["name"],
                "type": ward["ward_type"],
                "total": ward["total_beds"],
                "occupied": occupied,
                "available": ward["available_beds"],
                "occupancy_percentage": round(occupancy_pct, 2)
            })

        return success_response(
            data=occupancy_data,
            message="Ward occupancy retrieved successfully",
            code=200
        ), 200
