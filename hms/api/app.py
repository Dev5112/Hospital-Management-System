"""Flask application factory for the Hospital Management System REST API."""

from flask import Flask
from flask_restful import Api


def create_app(config=None):
    """Create and configure Flask application.

    Args:
        config: Configuration class (defaults to ACTIVE_CONFIG from hms.api.config)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config is None:
        from hms.api.config import ACTIVE_CONFIG
        config = ACTIVE_CONFIG

    app.config.from_object(config)

    # Initialize Flask-RESTful
    api = Api(app)

    # Register middleware
    from hms.api.middleware import register_all_middleware
    register_all_middleware(app)

    # Register resource blueprints
    _register_resources(api)

    return app


def _register_resources(api: Api) -> None:
    """Register all API resources with the API instance.

    Args:
        api: Flask-RESTful Api instance
    """
    # Auth resources
    from hms.api.resources.auth import LoginResource, LogoutResource

    api.add_resource(LoginResource, "/api/auth/login")
    api.add_resource(LogoutResource, "/api/auth/logout")

    # Doctor resources
    from hms.api.resources.doctors import DoctorListResource, DoctorResource, DoctorAppointmentsResource

    api.add_resource(DoctorListResource, "/api/doctors")
    api.add_resource(DoctorResource, "/api/doctors/<int:doctor_id>")
    api.add_resource(DoctorAppointmentsResource, "/api/doctors/<int:doctor_id>/appointments")

    # Patient resources
    from hms.api.resources.patients import (
        PatientListResource,
        PatientResource,
        PatientAppointmentsResource,
        PatientMedicalRecordsResource,
        PatientBillingResource
    )

    api.add_resource(PatientListResource, "/api/patients")
    api.add_resource(PatientResource, "/api/patients/<int:patient_id>")
    api.add_resource(PatientAppointmentsResource, "/api/patients/<int:patient_id>/appointments")
    api.add_resource(PatientMedicalRecordsResource, "/api/patients/<int:patient_id>/medical-records")
    api.add_resource(PatientBillingResource, "/api/patients/<int:patient_id>/billing")

    # Appointment resources
    from hms.api.resources.appointments import (
        AppointmentListResource,
        AppointmentResource,
        AppointmentAvailableSlotsResource,
        AppointmentTodayResource
    )

    api.add_resource(AppointmentListResource, "/api/appointments")
    api.add_resource(AppointmentResource, "/api/appointments/<int:appointment_id>")
    api.add_resource(AppointmentAvailableSlotsResource, "/api/appointments/available-slots")
    api.add_resource(AppointmentTodayResource, "/api/appointments/today")

    # Billing resources
    from hms.api.resources.billing import BillingListResource, BillingResource, BillingPaymentResource, BillingSummaryResource

    api.add_resource(BillingListResource, "/api/billing")
    api.add_resource(BillingResource, "/api/billing/<int:bill_id>")
    api.add_resource(BillingPaymentResource, "/api/billing/<int:bill_id>/pay")
    api.add_resource(BillingSummaryResource, "/api/billing/summary")

    # Ward resources
    from hms.api.resources.wards import WardListResource, WardResource, WardBedsResource, WardOccupancyResource

    api.add_resource(WardListResource, "/api/wards")
    api.add_resource(WardResource, "/api/wards/<int:ward_id>")
    api.add_resource(WardBedsResource, "/api/wards/<int:ward_id>/beds")
    api.add_resource(WardOccupancyResource, "/api/wards/occupancy")

    # Chart resources
    from hms.api.resources.charts import (
        AdminOverviewStatsResource,
        AdminAppointmentsTrendResource,
        AdminStatusBreakdownResource,
        AdminSpecializationsResource,
        AdminRevenueResource,
        AdminOccupancyResource,
        AdminPatientGenderResource,
        AdminAdmissionsTrendResource,
        AdminDiagnosesResource,
        DoctorAppointmentDistributionResource,
        DoctorStatusBreakdownResource,
        DoctorWeeklyHeatmapResource,
        DoctorTopDiagnosesResource,
        DoctorMonthlyPatientsResource,
        PatientTreatmentTimelineResource,
        PatientBillingHistoryResource,
        PatientVisitFrequencyResource,
        PatientDiagnosesResource,
        PatientKPIResource
    )

    # Admin chart endpoints
    api.add_resource(AdminOverviewStatsResource, "/api/charts/admin/overview")
    api.add_resource(AdminAppointmentsTrendResource, "/api/charts/admin/appointments-trend")
    api.add_resource(AdminStatusBreakdownResource, "/api/charts/admin/status-breakdown")
    api.add_resource(AdminSpecializationsResource, "/api/charts/admin/specializations")
    api.add_resource(AdminRevenueResource, "/api/charts/admin/revenue")
    api.add_resource(AdminOccupancyResource, "/api/charts/admin/occupancy")
    api.add_resource(AdminPatientGenderResource, "/api/charts/admin/gender")
    api.add_resource(AdminAdmissionsTrendResource, "/api/charts/admin/admissions-trend")
    api.add_resource(AdminDiagnosesResource, "/api/charts/admin/diagnoses")

    # Doctor chart endpoints
    api.add_resource(DoctorAppointmentDistributionResource, "/api/charts/doctor/appointment-distribution")
    api.add_resource(DoctorStatusBreakdownResource, "/api/charts/doctor/status-breakdown")
    api.add_resource(DoctorWeeklyHeatmapResource, "/api/charts/doctor/weekly-heatmap")
    api.add_resource(DoctorTopDiagnosesResource, "/api/charts/doctor/top-diagnoses")
    api.add_resource(DoctorMonthlyPatientsResource, "/api/charts/doctor/monthly-patients")

    # Patient chart endpoints
    api.add_resource(PatientTreatmentTimelineResource, "/api/charts/patient/timeline")
    api.add_resource(PatientBillingHistoryResource, "/api/charts/patient/billing")
    api.add_resource(PatientVisitFrequencyResource, "/api/charts/patient/visits")
    api.add_resource(PatientDiagnosesResource, "/api/charts/patient/diagnoses")
    api.add_resource(PatientKPIResource, "/api/charts/patient/kpi")
