"""
Configuration file for HMS AI/ML System.
All constants, thresholds, and model parameters defined here.
"""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ML Model Paths
DISEASE_PREDICTOR_MODEL = MODELS_DIR / "disease_predictor.joblib"
READMISSION_RISK_MODEL = MODELS_DIR / "readmission_risk.joblib"
BED_OPTIMIZER_MODEL = MODELS_DIR / "bed_optimizer.joblib"
APPOINTMENT_FORECASTER_MODEL = MODELS_DIR / "appointment_forecaster.joblib"
FRAUD_DETECTOR_IF_MODEL = MODELS_DIR / "fraud_detector_if.joblib"
FRAUD_DETECTOR_AE_MODEL = MODELS_DIR / "fraud_detector_ae.h5"
FRAUD_DETECTOR_CLASSIFIER = MODELS_DIR / "fraud_detector_classifier.joblib"
DRUG_INTERACTION_MODEL = MODELS_DIR / "drug_interaction.joblib"
DRUG_INTERACTION_DATA = DATA_DIR / "drug_interactions.csv"

# Synthetic Data Configuration
SYNTHETIC_DATA_CONFIG = {
    "n_patients": 5000,
    "n_appointments": 3000,
    "n_billing": 2000,
    "n_admissions": 2000,
    "n_drug_pairs": 500,
    "n_time_series_days": 365,
}

# Disease Predictor Configuration
DISEASE_PREDICTOR_CONFIG = {
    "symptoms_max_features": 100,
    "n_estimators": 200,
    "max_depth": 15,
    "learning_rate": 0.1,
    "random_state": 42,
    "diseases": [
        "Type 2 Diabetes",
        "Hypertension",
        "Anemia",
        "Pneumonia",
        "Dengue",
        "Malaria",
        "Typhoid",
        "COVID-19",
        "Heart Disease",
        "Kidney Disease",
    ],
}

# Readmission Risk Configuration
READMISSION_RISK_CONFIG = {
    "risk_thresholds": {
        "Low": (0, 30),
        "Medium": (30, 60),
        "High": (60, 80),
        "Critical": (80, 100),
    },
    "gb_n_estimators": 150,
    "gb_learning_rate": 0.1,
    "random_state": 42,
}

# Bed Optimizer Configuration
BED_OPTIMIZER_CONFIG = {
    "lstm_layers": 2,
    "lstm_units": 64,
    "lstm_epochs": 50,
    "lstm_batch_size": 16,
    "lstm_dropout": 0.2,
    "forecast_days": 7,
    "confidence_level": 0.95,
}

# Appointment Forecaster Configuration
APPOINTMENT_FORECASTER_CONFIG = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_split": 5,
    "random_state": 42,
    "no_show_threshold": 0.5,
}

# Fraud Detector Configuration
FRAUD_DETECTOR_CONFIG = {
    "if_n_estimators": 100,
    "if_contamination": 0.05,
    "ae_encoding_dim": 16,
    "ae_epochs": 50,
    "ae_batch_size": 32,
    "fraud_threshold": 0.7,
    "if_weight": 0.6,
    "ae_weight": 0.4,
}

# Drug Interaction Configuration
DRUG_INTERACTION_CONFIG = {
    "similarity_threshold": 0.7,
    "tfidf_max_features": 1000,
    "random_state": 42,
}

# Chatbot Configuration
CHATBOT_CONFIG = {
    "max_turns": 10,
    "auto_summary_after_turns": 5,
    "temperature": 0.7,
}

# Report Summarizer Configuration
REPORT_SUMMARIZER_CONFIG = {
    "temperature": 0.5,
    "max_tokens": 1000,
}

# Discharge Generator Configuration
DISCHARGE_GENERATOR_CONFIG = {
    "temperature": 0.6,
    "max_tokens": 1500,
}

# Alert Narrator Configuration
ALERT_NARRATOR_CONFIG = {
    "temperature": 0.6,
    "max_tokens": 800,
}

# Model Trainer Configuration
MODEL_TRAINER_CONFIG = {
    "test_size": 0.2,
    "random_state": 42,
    "log_file": LOGS_DIR / "ml_training_log.json",
}

# Data Validation Ranges
DATA_VALIDATION = {
    "age_min": 0,
    "age_max": 120,
    "bp_systolic_min": 80,
    "bp_systolic_max": 200,
    "temperature_min": 35.0,
    "temperature_max": 42.0,
    "heart_rate_min": 40,
    "heart_rate_max": 200,
    "blood_glucose_min": 40,
    "blood_glucose_max": 600,
    "bmi_min": 12.0,
    "bmi_max": 60.0,
}

# Visualization Configuration
VISUALIZATION_CONFIG = {
    "style": "seaborn-v0_8-darkgrid",
    "figsize": (12, 6),
    "dpi": 100,
    "font_size": 10,
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
