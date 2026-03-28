"""Billing management resources."""

from flask_restful import Resource
from flask import request
from datetime import datetime
from hms.api.database import APIDatabase
from hms.api.config import ACTIVE_CONFIG, DB_PATH, VALID_BILLING_STATUS
from hms.api.utils.response import success_response, error_response, validation_error_response, paginated_response
from hms.api.utils.validators import (
    validate_required_fields, validate_pagination_params, validate_positive_number,
    validate_billing_status
)
from hms.api.utils.auth_helper import token_required, role_required


db = APIDatabase(str(DB_PATH))


class BillingListResource(Resource):
    """GET /api/billing - List bills
    POST /api/billing - Create new bill"""

    @token_required
    @role_required("admin")
    def get(self):
        """Get all bills with filters.

        Query params:
            ?status=unpaid&patient_id=1&page=1&limit=10
        """
        status = request.args.get("status", "")
        patient_id = request.args.get("patient_id", "")
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)

        is_valid, error_msg = validate_pagination_params(page, limit)
        if not is_valid:
            return error_response(error_msg, code=400), 400

        offset = (page - 1) * limit

        query = """SELECT b.*, p.name as patient_name
                   FROM billing b
                   LEFT JOIN patients p ON b.patient_id = p.patient_id
                   WHERE 1=1"""
        params = []

        if status:
            query += " AND b.status = ?"
            params.append(status)

        if patient_id:
            query += " AND b.patient_id = ?"
            params.append(patient_id)

        count_query = query.replace("SELECT b.*", "SELECT COUNT(*)")
        total = db.count(count_query, tuple(params))

        query += f" ORDER BY b.billing_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        bills = db.execute_all(query, tuple(params))

        return paginated_response(
            data=bills,
            message="Bills retrieved successfully",
            page=page,
            page_size=limit,
            total=total,
            code=200
        ), 200

    @token_required
    @role_required("admin")
    def post(self):
        """Create new bill.

        Request body:
        {
            "patient_id": 1,
            "total_amount": 5000,
            "services": ["Consultation", "Lab Test"]
        }
        """
        data = request.get_json() or {}

        required_fields = ["patient_id", "total_amount"]
        missing = validate_required_fields(data, required_fields)
        if missing:
            return validation_error_response(missing), 400

        if not validate_positive_number(data["total_amount"]):
            return validation_error_response({"total_amount": "Must be a positive number"}), 400

        # Verify patient exists
        patient = db.execute_one("SELECT patient_id FROM patients WHERE patient_id = ?", (data["patient_id"],))
        if not patient:
            return error_response("Patient not found", code=404), 404

        services = data.get("services", [])
        services_str = ", ".join(services) if services else ""

        bill_id = db.execute(
            """INSERT INTO billing (patient_id, total_amount, services, status, paid_amount)
               VALUES (?, ?, ?, 'unpaid', 0)""",
            (data["patient_id"], float(data["total_amount"]), services_str)
        )

        if bill_id:
            bill = db.execute_one("SELECT * FROM billing WHERE bill_id = ?", (bill_id,))
            return success_response(
                data=bill,
                message="Bill created successfully",
                code=201
            ), 201

        return error_response("Failed to create bill", code=500), 500


class BillingResource(Resource):
    """GET /api/billing/<id> - Get bill"""

    def get(self, bill_id: int):
        """Get single bill with itemized details."""
        bill = db.execute_one(
            """SELECT b.*, p.name as patient_name
               FROM billing b
               LEFT JOIN patients p ON b.patient_id = p.patient_id
               WHERE b.bill_id = ?""",
            (bill_id,)
        )

        if not bill:
            return error_response("Bill not found", code=404), 404

        bill["remaining_balance"] = bill["total_amount"] - bill.get("paid_amount", 0)

        return success_response(
            data=bill,
            message="Bill retrieved successfully",
            code=200
        ), 200


class BillingPaymentResource(Resource):
    """PATCH /api/billing/<id>/pay - Record payment"""

    @token_required
    @role_required("admin")
    def patch(self, bill_id: int):
        """Record payment for a bill.

        Request body:
        {
            "amount": 2000,
            "payment_method": "cash"
        }
        """
        bill = db.execute_one("SELECT * FROM billing WHERE bill_id = ?", (bill_id,))

        if not bill:
            return error_response("Bill not found", code=404), 404

        data = request.get_json() or {}

        if "amount" not in data:
            return validation_error_response({"amount": "Amount is required"}), 400

        if not validate_positive_number(data["amount"]):
            return validation_error_response({"amount": "Must be a positive number"}), 400

        payment_amount = float(data["amount"])
        current_paid = bill.get("paid_amount", 0) or 0
        new_paid = current_paid + payment_amount

        if new_paid > bill["total_amount"]:
            return error_response(
                f"Payment exceeds bill amount. Bill total: {bill['total_amount']}, already paid: {current_paid}",
                code=400
            ), 400

        # Determine new status
        if new_paid >= bill["total_amount"]:
            new_status = "paid"
        elif new_paid > 0:
            new_status = "partial"
        else:
            new_status = "unpaid"

        payment_method = data.get("payment_method", "cash")
        payment_date = datetime.now().isoformat()

        db.execute(
            """UPDATE billing SET paid_amount = ?, status = ?, payment_method = ?, payment_date = ?
               WHERE bill_id = ?""",
            (new_paid, new_status, payment_method, payment_date, bill_id)
        )

        updated_bill = db.execute_one("SELECT * FROM billing WHERE bill_id = ?", (bill_id,))
        updated_bill["remaining_balance"] = updated_bill["total_amount"] - updated_bill["paid_amount"]

        return success_response(
            data=updated_bill,
            message="Payment recorded successfully",
            code=200
        ), 200


class BillingSummaryResource(Resource):
    """GET /api/billing/summary - Admin summary"""

    @token_required
    @role_required("admin")
    def get(self):
        """Get billing summary statistics."""
        summary = db.execute_one(
            """SELECT
               SUM(total_amount) as total_revenue,
               SUM(paid_amount) as total_paid,
               SUM(CASE WHEN status = 'unpaid' THEN 1 ELSE 0 END) as unpaid_count,
               SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
               SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial_count,
               SUM(CASE WHEN status != 'paid' THEN total_amount - COALESCE(paid_amount, 0) ELSE 0 END) as outstanding_amount
               FROM billing"""
        )

        summary = dict(summary) if summary else {}

        return success_response(
            data={
                "total_revenue": summary.get("total_revenue", 0),
                "total_paid": summary.get("total_paid", 0),
                "outstanding_amount": summary.get("outstanding_amount", 0),
                "unpaid_bills": summary.get("unpaid_count", 0),
                "partial_bills": summary.get("partial_count", 0),
                "paid_bills": summary.get("paid_count", 0)
            },
            message="Billing summary retrieved successfully",
            code=200
        ), 200
