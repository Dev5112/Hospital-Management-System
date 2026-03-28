"""Flask-RESTful resources for chart and dashboard API endpoints."""

from flask import request, g
from flask_restful import Resource
from hms.api.database import APIDatabase
from hms.api.config import DB_PATH
from hms.api.utils.response import success_response, error_response
from hms.api.utils.auth_helper import token_required, role_required
from hms.api.utils.chart_queries import (
    AdminChartQueries,
    DoctorChartQueries,
    PatientChartQueries
)


# Initialize database instance
db = APIDatabase(str(DB_PATH))


# ============================================================================
# ADMIN DASHBOARD RESOURCES
# ============================================================================

class AdminOverviewStatsResource(Resource):
    """Admin dashboard overview statistics."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get admin overview KPI statistics."""
        try:
            data = AdminChartQueries.get_overview_stats(db)
            return success_response(
                data=data,
                message="Admin overview stats retrieved"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminAppointmentsTrendResource(Resource):
    """Admin appointments trend chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get appointment trend data for specified period."""
        try:
            # Map period parameter to days
            period = request.args.get('period', '30d')
            days_map = {'7d': 7, '30d': 30, '90d': 90}
            days = days_map.get(period, 30)

            data = AdminChartQueries.get_appointments_trend(db, days)

            return success_response(
                data={
                    'labels': [item['date'] for item in data],
                    'datasets': [{
                        'label': 'Appointments',
                        'data': [item['count'] for item in data],
                        'borderColor': '#4F9CF9',
                        'backgroundColor': 'rgba(79,156,249,0.1)',
                        'tension': 0.1,
                        'fill': True
                    }]
                },
                message=f"Appointment trend for {period}"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminStatusBreakdownResource(Resource):
    """Admin appointment status breakdown chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get appointment status breakdown."""
        try:
            data = AdminChartQueries.get_appointments_by_status(db)

            status_colors = {
                'scheduled': '#4F9CF9',
                'completed': '#22C55E',
                'cancelled': '#EF4444'
            }

            return success_response(
                data={
                    'labels': [item['status'].capitalize() for item in data],
                    'datasets': [{
                        'data': [item['count'] for item in data],
                        'backgroundColor': [status_colors.get(item['status'], '#999') for item in data],
                        'borderColor': '#fff',
                        'borderWidth': 2
                    }]
                },
                message="Appointment status breakdown"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminSpecializationsResource(Resource):
    """Admin top specializations chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get top specializations by appointment count."""
        try:
            data = AdminChartQueries.get_top_specializations(db)

            return success_response(
                data={
                    'labels': [item['specialization'] for item in data],
                    'datasets': [{
                        'label': 'Appointments',
                        'data': [item['count'] for item in data],
                        'backgroundColor': '#4F9CF9',
                        'borderColor': '#2563EB',
                        'borderWidth': 1
                    }]
                },
                message="Top specializations"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminRevenueResource(Resource):
    """Admin monthly revenue chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get monthly revenue data."""
        try:
            from datetime import datetime
            year = request.args.get('year', str(datetime.now().year))

            data = AdminChartQueries.get_revenue_by_month(db, int(year))

            # Ensure all 12 months are present
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            revenue_by_month = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0,
                               7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0}

            for item in data:
                if item['month'] is not None:
                    revenue_by_month[int(item['month'])] = float(item['total_amount'] or 0)

            return success_response(
                data={
                    'labels': month_names,
                    'datasets': [{
                        'label': 'Revenue (₹)',
                        'data': [revenue_by_month[i] for i in range(1, 13)],
                        'backgroundColor': 'rgba(34,197,94,0.1)',
                        'borderColor': '#22C55E',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
                    }]
                },
                message="Monthly revenue"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminOccupancyResource(Resource):
    """Admin bed occupancy by ward chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get bed occupancy by ward type."""
        try:
            data = AdminChartQueries.get_bed_occupancy_by_ward(db)

            return success_response(
                data={
                    'labels': [item['ward_type'].capitalize() for item in data],
                    'datasets': [{
                        'label': 'Occupancy %',
                        'data': [float(item['occupancy_percent']) for item in data],
                        'borderColor': '#4F9CF9',
                        'backgroundColor': 'rgba(79,156,249,0.5)',
                        'pointBackgroundColor': '#4F9CF9',
                        'pointBorderColor': '#fff',
                        'pointBorderWidth': 2,
                        'pointRadius': 5
                    }]
                },
                message="Bed occupancy by ward"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminPatientGenderResource(Resource):
    """Admin patient gender split chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get patient count by gender."""
        try:
            data = AdminChartQueries.get_patient_gender_split(db)

            gender_labels = {'M': 'Male', 'F': 'Female', 'Other': 'Other'}
            gender_colors = {'M': '#4F9CF9', 'F': '#EC4899', 'Other': '#F59E0B'}

            return success_response(
                data={
                    'labels': [gender_labels.get(item['gender'], item['gender']) for item in data],
                    'datasets': [{
                        'data': [item['count'] for item in data],
                        'backgroundColor': [gender_colors.get(item['gender'], '#999') for item in data],
                        'borderColor': '#fff',
                        'borderWidth': 2
                    }]
                },
                message="Patient gender split"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminAdmissionsTrendResource(Resource):
    """Admin admissions vs discharges trend chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get daily admissions vs discharges."""
        try:
            days = request.args.get('days', 30, type=int)
            data = AdminChartQueries.get_admissions_vs_discharges(db, days)

            return success_response(
                data={
                    'labels': [item['date'] for item in data],
                    'datasets': [
                        {
                            'label': 'Admissions',
                            'data': [item['admissions'] for item in data],
                            'borderColor': '#F59E0B',
                            'backgroundColor': 'rgba(245,158,11,0.1)',
                            'tension': 0.1,
                            'fill': True
                        },
                        {
                            'label': 'Discharges',
                            'data': [item['discharges'] for item in data],
                            'borderColor': '#22C55E',
                            'backgroundColor': 'rgba(34,197,94,0.1)',
                            'tension': 0.1,
                            'fill': True
                        }
                    ]
                },
                message="Admissions vs discharges trend"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class AdminDiagnosesResource(Resource):
    """Admin top diagnoses chart."""

    @token_required
    @role_required('admin')
    def get(self):
        """Get top diagnoses."""
        try:
            limit = request.args.get('limit', 10, type=int)
            data = AdminChartQueries.get_top_diagnoses(db, limit)

            return success_response(
                data={
                    'labels': [item['diagnosis'] for item in data],
                    'datasets': [{
                        'label': 'Count',
                        'data': [item['count'] for item in data],
                        'backgroundColor': '#A855F7',
                        'borderColor': '#7E22CE',
                        'borderWidth': 1
                    }]
                },
                message="Top diagnoses"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


# ============================================================================
# DOCTOR DASHBOARD RESOURCES
# ============================================================================

class DoctorAppointmentDistributionResource(Resource):
    """Doctor appointment distribution chart."""

    @token_required
    @role_required('doctor')
    def get(self):
        """Get doctor's appointment distribution by day of week."""
        try:
            doctor_id = request.args.get('doctor_id', type=int)
            if not doctor_id:
                return error_response("doctor_id parameter required", code=400), 400

            data = DoctorChartQueries.get_doctor_appointment_distribution(db, doctor_id)

            return success_response(
                data={
                    'labels': [item['day_of_week'] for item in data],
                    'datasets': [{
                        'label': 'Appointments',
                        'data': [item['count'] for item in data],
                        'backgroundColor': '#4F9CF9',
                        'borderColor': '#2563EB',
                        'borderWidth': 1
                    }]
                },
                message="Appointment distribution by day"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class DoctorStatusBreakdownResource(Resource):
    """Doctor appointment status breakdown chart."""

    @token_required
    @role_required('doctor')
    def get(self):
        """Get doctor's appointment status breakdown."""
        try:
            doctor_id = request.args.get('doctor_id', type=int)
            if not doctor_id:
                return error_response("doctor_id parameter required", code=400), 400

            data = DoctorChartQueries.get_doctor_status_breakdown(db, doctor_id)

            status_colors = {
                'scheduled': '#4F9CF9',
                'completed': '#22C55E',
                'cancelled': '#EF4444'
            }

            return success_response(
                data={
                    'labels': [item['status'].capitalize() for item in data],
                    'datasets': [{
                        'data': [item['count'] for item in data],
                        'backgroundColor': [status_colors.get(item['status'], '#999') for item in data],
                        'borderColor': '#fff',
                        'borderWidth': 2
                    }]
                },
                message="Appointment status breakdown"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class DoctorWeeklyHeatmapResource(Resource):
    """Doctor weekly schedule heatmap."""

    @token_required
    @role_required('doctor')
    def get(self):
        """Get doctor's weekly schedule heatmap."""
        try:
            doctor_id = request.args.get('doctor_id', type=int)
            if not doctor_id:
                return error_response("doctor_id parameter required", code=400), 400

            heatmap = DoctorChartQueries.get_doctor_weekly_heatmap(db, doctor_id)

            return success_response(
                data=heatmap,
                message="Weekly schedule heatmap"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class DoctorTopDiagnosesResource(Resource):
    """Doctor top diagnoses chart."""

    @token_required
    @role_required('doctor')
    def get(self):
        """Get doctor's top diagnoses."""
        try:
            doctor_id = request.args.get('doctor_id', type=int)
            if not doctor_id:
                return error_response("doctor_id parameter required", code=400), 400

            data = DoctorChartQueries.get_doctor_top_diagnoses(db, doctor_id)

            return success_response(
                data={
                    'labels': [item['diagnosis'] for item in data],
                    'datasets': [{
                        'data': [item['count'] for item in data],
                        'backgroundColor': ['#4F9CF9', '#22C55E', '#F59E0B', '#EF4444', '#A855F7'],
                        'borderColor': '#fff',
                        'borderWidth': 2
                    }]
                },
                message="Top diagnoses"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class DoctorMonthlyPatientsResource(Resource):
    """Doctor monthly patient count chart."""

    @token_required
    @role_required('doctor')
    def get(self):
        """Get doctor's monthly patient count."""
        try:
            doctor_id = request.args.get('doctor_id', type=int)
            if not doctor_id:
                return error_response("doctor_id parameter required", code=400), 400

            data = DoctorChartQueries.get_doctor_monthly_patients(db, doctor_id)

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            patients_by_month = {i: 0 for i in range(1, 13)}

            for item in data:
                if item['month'] is not None:
                    patients_by_month[int(item['month'])] = item['count']

            return success_response(
                data={
                    'labels': month_names,
                    'datasets': [{
                        'label': 'Patients',
                        'data': [patients_by_month[i] for i in range(1, 13)],
                        'borderColor': '#4F9CF9',
                        'backgroundColor': 'rgba(79,156,249,0.1)',
                        'tension': 0.1,
                        'fill': True
                    }]
                },
                message="Monthly patient count"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


# ============================================================================
# PATIENT DASHBOARD RESOURCES
# ============================================================================

class PatientTreatmentTimelineResource(Resource):
    """Patient treatment history timeline."""

    @token_required
    @role_required('patient')
    def get(self):
        """Get patient's treatment history timeline."""
        try:
            patient_id = request.args.get('patient_id', type=int)
            if not patient_id:
                return error_response("patient_id parameter required", code=400), 400

            data = PatientChartQueries.get_patient_treatment_timeline(db, patient_id)

            return success_response(
                data={'events': data},
                message="Treatment history timeline"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class PatientBillingHistoryResource(Resource):
    """Patient billing history chart."""

    @token_required
    @role_required('patient')
    def get(self):
        """Get patient's billing history."""
        try:
            patient_id = request.args.get('patient_id', type=int)
            if not patient_id:
                return error_response("patient_id parameter required", code=400), 400

            data = PatientChartQueries.get_patient_billing_history(db, patient_id)

            return success_response(
                data={
                    'labels': [item['month'] for item in data],
                    'datasets': [
                        {
                            'label': 'Total Billed',
                            'data': [float(item['total_billed'] or 0) for item in data],
                            'borderColor': '#F59E0B',
                            'backgroundColor': 'rgba(245,158,11,0.1)',
                            'tension': 0.1,
                            'fill': True
                        },
                        {
                            'label': 'Amount Paid',
                            'data': [float(item['amount_paid'] or 0) for item in data],
                            'borderColor': '#22C55E',
                            'backgroundColor': 'rgba(34,197,94,0.1)',
                            'tension': 0.1,
                            'fill': True
                        }
                    ]
                },
                message="Billing history"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class PatientVisitFrequencyResource(Resource):
    """Patient visit frequency chart."""

    @token_required
    @role_required('patient')
    def get(self):
        """Get patient's visit frequency over last 12 months."""
        try:
            patient_id = request.args.get('patient_id', type=int)
            if not patient_id:
                return error_response("patient_id parameter required", code=400), 400

            data = PatientChartQueries.get_patient_visit_frequency(db, patient_id)

            return success_response(
                data={
                    'labels': [item['month'] for item in data],
                    'datasets': [{
                        'label': 'Visits',
                        'data': [item['count'] for item in data],
                        'backgroundColor': '#4F9CF9',
                        'borderColor': '#2563EB',
                        'borderWidth': 1
                    }]
                },
                message="Visit frequency"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class PatientDiagnosesResource(Resource):
    """Patient diagnosis breakdown chart."""

    @token_required
    @role_required('patient')
    def get(self):
        """Get patient's diagnosis breakdown."""
        try:
            patient_id = request.args.get('patient_id', type=int)
            if not patient_id:
                return error_response("patient_id parameter required", code=400), 400

            data = PatientChartQueries.get_patient_diagnosis_breakdown(db, patient_id)

            palette = ['#4F9CF9', '#22C55E', '#F59E0B', '#EF4444', '#A855F7', '#14B8A6', '#F97316', '#EC4899']

            return success_response(
                data={
                    'labels': [item['diagnosis'] for item in data],
                    'datasets': [{
                        'data': [item['count'] for item in data],
                        'backgroundColor': [palette[i % len(palette)] for i in range(len(data))],
                        'borderColor': '#fff',
                        'borderWidth': 2
                    }]
                },
                message="Diagnosis breakdown"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500


class PatientKPIResource(Resource):
    """Patient KPI metrics."""

    @token_required
    @role_required('patient')
    def get(self):
        """Get patient's KPI metrics."""
        try:
            patient_id = request.args.get('patient_id', type=int)
            if not patient_id:
                return error_response("patient_id parameter required", code=400), 400

            kpis = {
                'total_visits': PatientChartQueries.get_patient_total_visits(db, patient_id),
                'outstanding_balance': PatientChartQueries.get_patient_outstanding_balance(db, patient_id),
                'last_visit': PatientChartQueries.get_patient_last_visit(db, patient_id)
            }

            return success_response(
                data=kpis,
                message="Patient KPI metrics"
            ), 200
        except Exception as e:
            return error_response(str(e), code=500), 500
