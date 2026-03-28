"""Standardized JSON response builder for the REST API."""

from typing import Any, Dict, Optional, List


def success_response(
    data: Any,
    message: str = "Success",
    code: int = 200,
    pagination: Optional[Dict] = None
) -> Dict:
    """Build a standardized success response.

    Args:
        data: Response data
        message: Success message
        code: HTTP status code
        pagination: Optional pagination metadata

    Returns:
        Standardized response dictionary
    """
    response = {
        "status": "success",
        "code": code,
        "data": data,
        "message": message
    }
    if pagination:
        response["pagination"] = pagination
    return response


def error_response(
    message: str,
    code: int = 400,
    errors: Optional[Dict[str, str]] = None
) -> Dict:
    """Build a standardized error response.

    Args:
        message: Error message
        code: HTTP status code
        errors: Optional field-level error details

    Returns:
        Standardized error response dictionary
    """
    response = {
        "status": "error",
        "code": code,
        "data": None,
        "message": message
    }
    if errors:
        response["errors"] = errors
    return response


def validation_error_response(errors: Dict[str, str]) -> Dict:
    """Build a validation error response.

    Args:
        errors: Dictionary of field-level errors

    Returns:
        Validation error response
    """
    return error_response(
        message="Validation failed",
        code=400,
        errors=errors
    )


def paginated_response(
    data: List,
    message: str = "Data retrieved successfully",
    page: int = 1,
    page_size: int = 10,
    total: int = 0,
    code: int = 200
) -> Dict:
    """Build a paginated response.

    Args:
        data: List of items
        message: Success message
        page: Current page number
        page_size: Items per page
        total: Total number of items
        code: HTTP status code

    Returns:
        Response with pagination metadata
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return success_response(
        data=data,
        message=message,
        code=code,
        pagination={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    )
