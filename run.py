"""Entry point to run the Hospital Management System REST API."""

import os
from hms.api import create_app
from hms.api.config import DevelopmentConfig

if __name__ == "__main__":
    # Determine debug mode
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")

    # Create Flask app
    app = create_app(DevelopmentConfig)

    # Print API endpoints info
    print("\n" + "="*60)
    print("Hospital Management System REST API")
    print("="*60)
    print(f"\nStarting server at http://{host}:{port}")
    print(f"Debug mode: {debug}\n")

    print("Available Endpoints:")
    print("─" * 60)

    # Auth
    print("\nAuthentication:")
    print("  POST   /api/auth/login")
    print("  POST   /api/auth/logout")

    # Doctors
    print("\nDoctors:")
    print("  GET    /api/doctors")
    print("  POST   /api/doctors")
    print("  GET    /api/doctors/<id>")
    print("  PUT    /api/doctors/<id>")
    print("  PATCH  /api/doctors/<id>")
    print("  DELETE /api/doctors/<id>")
    print("  GET    /api/doctors/<id>/appointments")

    # Patients
    print("\nPatients:")
    print("  GET    /api/patients")
    print("  POST   /api/patients")
    print("  GET    /api/patients/<id>")
    print("  PUT    /api/patients/<id>")
    print("  PATCH  /api/patients/<id>")
    print("  DELETE /api/patients/<id>")
    print("  GET    /api/patients/<id>/appointments")
    print("  GET    /api/patients/<id>/medical-records")
    print("  GET    /api/patients/<id>/billing")

    # Appointments
    print("\nAppointments:")
    print("  GET    /api/appointments")
    print("  POST   /api/appointments")
    print("  GET    /api/appointments/<id>")
    print("  PUT    /api/appointments/<id>")
    print("  PATCH  /api/appointments/<id>")
    print("  DELETE /api/appointments/<id>")
    print("  GET    /api/appointments/today")
    print("  GET    /api/appointments/available-slots")

    # Billing
    print("\nBilling:")
    print("  GET    /api/billing")
    print("  POST   /api/billing")
    print("  GET    /api/billing/<id>")
    print("  PATCH  /api/billing/<id>/pay")
    print("  GET    /api/billing/summary")

    # Wards
    print("\nWards:")
    print("  GET    /api/wards")
    print("  POST   /api/wards")
    print("  GET    /api/wards/<id>")
    print("  PATCH  /api/wards/<id>/beds")
    print("  GET    /api/wards/occupancy")

    print("\n" + "="*60 + "\n")

    # Run the Flask development server
    app.run(
        host=host,
        port=port,
        debug=debug
    )
