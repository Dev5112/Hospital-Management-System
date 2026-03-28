"""Input validation utilities for the REST API."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email string to validate

    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number (10 digits).

    Args:
        phone: Phone number string

    Returns:
        True if valid (10 digits), False otherwise
    """
    digits_only = ''.join(filter(str.isdigit, phone))
    return len(digits_only) == 10


def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    """Validate date string format.

    Args:
        date_str: Date string to validate
        fmt: Expected date format

    Returns:
        True if valid date format, False otherwise
    """
    try:
        datetime.strptime(date_str, fmt)
        return True
    except (ValueError, TypeError):
        return False


def validate_date_not_past(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    """Validate that date is not in the past.

    Args:
        date_str: Date string to validate
        fmt: Expected date format

    Returns:
        True if date is today or in future, False if in past
    """
    try:
        date_obj = datetime.strptime(date_str, fmt).date()
        from datetime import date as date_class
        return date_obj >= date_class.today()
    except (ValueError, TypeError):
        return False


def validate_blood_group(bg: str) -> bool:
    """Validate blood group.

    Args:
        bg: Blood group string

    Returns:
        True if valid blood group, False otherwise
    """
    valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    return bg in valid_groups


def validate_time_slot(slot: str) -> bool:
    """Validate time slot (30-min intervals 09:00-17:30).

    Args:
        slot: Time slot string (HH:MM format)

    Returns:
        True if valid time slot, False otherwise
    """
    valid_slots = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
        "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"
    ]
    return slot in valid_slots


def validate_gender(gender: str) -> bool:
    """Validate gender value.

    Args:
        gender: Gender string

    Returns:
        True if valid gender, False otherwise
    """
    return gender in ["M", "F", "Other"]


def validate_required_fields(data: Dict, required: List[str]) -> Dict[str, str]:
    """Validate that required fields are present and not empty.

    Args:
        data: Dictionary to validate
        required: List of required field names

    Returns:
        Dictionary of field names to error messages (empty if all valid)
    """
    errors = {}
    for field in required:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            errors[field] = f"{field} is required"
    return errors


def validate_appointment_status(status: str) -> bool:
    """Validate appointment status value.

    Args:
        status: Status string

    Returns:
        True if valid status, False otherwise
    """
    return status in ["scheduled", "completed", "cancelled"]


def validate_billing_status(status: str) -> bool:
    """Validate billing status value.

    Args:
        status: Status string

    Returns:
        True if valid status, False otherwise
    """
    return status in ["unpaid", "partial", "paid"]


def validate_positive_number(value: Any) -> bool:
    """Validate that value is a positive number.

    Args:
        value: Value to validate

    Returns:
        True if positive number, False otherwise
    """
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_age(age: int) -> bool:
    """Validate age is reasonable (0-150).

    Args:
        age: Age to validate

    Returns:
        True if valid age, False otherwise
    """
    try:
        age_int = int(age)
        return 0 <= age_int <= 150
    except (ValueError, TypeError):
        return False


def validate_pagination_params(page: Any, page_size: Any) -> Tuple[bool, Optional[str]]:
    """Validate pagination parameters.

    Args:
        page: Page number
        page_size: Items per page

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        page_int = int(page) if page else 1
        page_size_int = int(page_size) if page_size else 10

        if page_int < 1:
            return False, "Page must be >= 1"
        if page_size_int < 1 or page_size_int > 100:
            return False, "Page size must be between 1 and 100"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid pagination parameters"


# Type hint helper
from typing import Any
