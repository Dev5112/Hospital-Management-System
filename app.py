#!/usr/bin/env python3
"""
Hospital Management System - Flask Application Entry Point

Run this file to start the HMS Flask server.

Usage:
    python app.py

The application will be available at http://localhost:5000/
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from hms.api.app import create_app


def main():
    """Create and run the Flask application."""
    app = create_app()

    # Configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║  Hospital Management System - Flask API Server             ║
    ╚════════════════════════════════════════════════════════════╝

    Starting HMS Flask Server...

    Configuration:
    • Host: {host}
    • Port: {port}
    • Debug: {debug}

    API Documentation:
    • Base URL: http://{host}:{port}
    • Chart Endpoints: /api/charts/*
    • Admin Dashboard: /dashboard/admin
    • Doctor Dashboard: /dashboard/doctor
    • Patient Dashboard: /dashboard/patient

    Press CTRL+C to stop the server.
    """)

    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
