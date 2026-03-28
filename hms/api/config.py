"""API Configuration for Hospital Management System REST API."""

import os
from pathlib import Path
from datetime import timedelta

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent

# Database
DB_PATH = os.getenv("DB_PATH", BASE_DIR / "hms.db")
if isinstance(DB_PATH, str):
    DB_PATH = str(DB_PATH)

# Flask Configuration
class Config:
    """Base configuration."""
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DB_PATH = ":memory:"

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)

# API Response Settings
API_PAGE_SIZE_DEFAULT = 10
API_PAGE_SIZE_MAX = 100

# Validation Constants
VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
VALID_TIME_SLOTS = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
    "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"
]
VALID_GENDERS = ["M", "F", "Other"]
VALID_APPOINTMENT_STATUS = ["scheduled", "completed", "cancelled"]
VALID_BILLING_STATUS = ["unpaid", "partial", "paid"]
VALID_WARD_TYPES = ["General", "ICU", "Pediatric", "Maternity", "Isolation"]

# Default User Credentials (for demo - should be changed)
DEFAULT_CREDENTIALS = {
    "admin": {"password": "admin123", "role": "admin"},
    "doctor": {"password": "doctor123", "role": "doctor"},
    "patient": {"password": "patient123", "role": "patient"},
}

# Select config based on environment
ENV = os.getenv("FLASK_ENV", "development")
if ENV == "testing":
    ACTIVE_CONFIG = TestingConfig
elif ENV == "production":
    ACTIVE_CONFIG = ProductionConfig
else:
    ACTIVE_CONFIG = DevelopmentConfig
