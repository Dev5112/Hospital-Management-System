"""Authentication resources for login and logout."""

from flask_restful import Resource, reqparse
from flask import request, g
from hms.api.config import DEFAULT_CREDENTIALS, JWT_EXPIRATION_HOURS
from hms.api.utils.response import success_response, error_response
from hms.api.utils.auth_helper import encode_token, token_required, get_token_from_request, add_token_to_blacklist


class LoginResource(Resource):
    """POST /api/auth/login - Authenticate user and return JWT token."""

    def post(self):
        """Login with username and password.

        Request body:
        {
            "username": "admin",
            "password": "admin123"
        }

        Returns:
            Token and user details if successful, error otherwise
        """
        data = request.get_json() or {}

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return error_response(
                "Username and password are required",
                code=400,
                errors={"username": "required", "password": "required"}
            ), 400

        # Check credentials against defaults
        if username not in DEFAULT_CREDENTIALS:
            return error_response("Invalid username or password", code=401), 401

        cred = DEFAULT_CREDENTIALS[username]
        if cred["password"] != password:
            return error_response("Invalid username or password", code=401), 401

        # Generate token
        user_data = {
            "user_id": hash(username) % 10000,  # Simple hash for demo
            "username": username,
            "role": cred["role"]
        }

        token = encode_token(user_data)

        return success_response(
            data={
                "token": token,
                "username": username,
                "role": cred["role"],
                "expires_in": JWT_EXPIRATION_HOURS * 3600
            },
            message="Login successful",
            code=200
        ), 200


class LogoutResource(Resource):
    """POST /api/auth/logout - Invalidate JWT token."""

    @token_required
    def post(self):
        """Logout by invalidating token.

        Headers:
            Authorization: Bearer <token>

        Returns:
            Success message
        """
        token = get_token_from_request()
        if token:
            add_token_to_blacklist(token)

        return success_response(
            data=None,
            message="Logout successful",
            code=200
        ), 200
