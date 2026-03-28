"""JWT authentication helper functions."""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, g
from hms.api.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_DELTA
from hms.api.utils.response import error_response


def encode_token(user_data: Dict) -> str:
    """Encode JWT token with user data.

    Args:
        user_data: Dictionary with user_id and role

    Returns:
        Encoded JWT token string
    """
    payload = {
        "user_id": user_data.get("user_id"),
        "role": user_data.get("role"),
        "username": user_data.get("username"),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """Decode JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dictionary or None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_request() -> Optional[str]:
    """Extract JWT token from Authorization header.

    Expected format: Authorization: Bearer <token>

    Returns:
        Token string or None if not found
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def token_required(f):
    """Decorator to require valid JWT token on endpoint.

    Validates token and attaches current_user to g object.

    Returns:
        401 if token missing or invalid
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()

        if not token:
            return error_response("Missing authorization token", code=401), 401

        payload = decode_token(token)
        if not payload:
            return error_response("Invalid or expired token", code=401), 401

        g.current_user = payload
        return f(*args, **kwargs)

    return decorated_function


def role_required(*allowed_roles):
    """Decorator to require specific role on endpoint.

    Must be used after token_required decorator.

    Args:
        allowed_roles: Tuple of role strings that are allowed

    Returns:
        403 if user role not in allowed_roles
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, "current_user"):
                return error_response("Authentication required", code=401), 401

            user_role = g.current_user.get("role")
            if user_role not in allowed_roles:
                return error_response("Insufficient permissions", code=403), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


# Token blacklist for logout (in-memory)
_token_blacklist = set()


def add_token_to_blacklist(token: str) -> None:
    """Add token to blacklist on logout.

    Args:
        token: Token to blacklist
    """
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted.

    Args:
        token: Token to check

    Returns:
        True if token is in blacklist, False otherwise
    """
    return token in _token_blacklist
