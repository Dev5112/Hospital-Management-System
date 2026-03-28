"""Middleware for error handling, CORS, and logging."""

import logging
from flask import Flask, request
from hms.api.utils.response import error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for all HTTP errors.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        logger.warning(f"Bad request: {error}")
        return error_response("Bad request", code=400), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized."""
        logger.warning(f"Unauthorized: {error}")
        return error_response("Unauthorized", code=401), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden."""
        logger.warning(f"Forbidden: {error}")
        return error_response("Forbidden", code=403), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        logger.info(f"Resource not found: {error}")
        return error_response("Resource not found", code=404), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed."""
        logger.warning(f"Method not allowed: {error}")
        return error_response("Method not allowed", code=405), 405

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal error: {error}", exc_info=True)
        return error_response("Internal server error", code=500), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions."""
        logger.error(f"Uncaught exception: {error}", exc_info=True)
        return error_response("Internal server error", code=500), 500


def register_logging_middleware(app: Flask) -> None:
    """Register request/response logging middleware.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def log_request():
        """Log incoming request."""
        logger.info(f"{request.method} {request.path} - IP: {request.remote_addr}")

    @app.after_request
    def log_response(response):
        """Log outgoing response."""
        logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        return response


def register_cors_headers(app: Flask) -> None:
    """Register CORS headers in response.

    Note: Better to use flask-cors extension, but this is a fallback.

    Args:
        app: Flask application instance
    """

    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses."""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Content-Type"] = "application/json"
        return response


def register_all_middleware(app: Flask) -> None:
    """Register all middleware components.

    Args:
        app: Flask application instance
    """
    register_logging_middleware(app)
    register_error_handlers(app)
    register_cors_headers(app)
