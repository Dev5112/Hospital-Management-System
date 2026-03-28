"""
Appointment No-Show Predictor using Random Forest.
Predicts probability of patient no-shows and provides intervention strategies.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from typing import Dict, Any
import sys
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import APPOINTMENT_FORECASTER_MODEL, APPOINTMENT_FORECASTER_CONFIG


class AppointmentForecaster:
    """
    Random Forest-based no-show predictor with calibrated probabilities.
    """

    def __init__(self):
        """Initialize appointment forecaster."""
        self.model = None
        self.is_trained = False

    def preprocess(self, raw_input: dict) -> pd.DataFrame:
        """
        Preprocess appointment data.

        Args:
            raw_input: Dictionary with appointment features

        Returns:
            DataFrame with processed features
        """
        patient_age = raw_input.get("patient_age", 40)
        appointment_type = raw_input.get("appointment_type", "routine")
        day_of_week = raw_input.get("day_of_week", "Monday")
        time_of_day = raw_input.get("time_of_day", "morning")
        lead_time_days = raw_input.get("lead_time_days", 7)
        previous_no_shows = raw_input.get("previous_no_shows", 0)
        previous_appointments = raw_input.get("previous_appointments", 1)
        distance_km = raw_input.get("distance_km", 5.0)
        insurance_type = raw_input.get("insurance_type", "Private")
        reminder_sent = raw_input.get("reminder_sent", True)

        # Encode categorical variables
        appointment_type_map = {"routine": 0, "follow-up": 1, "specialist": 2, "emergency": 3}
        time_map = {"morning": 0, "afternoon": 1, "evening": 2}
        day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        insurance_map = {"Private": 0, "Government": 1, "None": 2}

        features_dict = {
            "patient_age": [patient_age],
            "appointment_type": [appointment_type_map.get(appointment_type, 0)],
            "day_of_week": [day_map.get(day_of_week, 0)],
            "time_of_day": [time_map.get(time_of_day, 0)],
            "lead_time_days": [lead_time_days],
            "previous_no_shows": [previous_no_shows],
            "previous_appointments": [previous_appointments],
            "distance_km": [distance_km],
            "insurance_type": [insurance_map.get(insurance_type, 0)],
            "reminder_sent": [int(reminder_sent)],
        }

        return pd.DataFrame(features_dict)

    def train(self, df: pd.DataFrame) -> None:
        """
        Train the no-show predictor.

        Args:
            df: Training DataFrame with appointment data
        """
        print("Training Appointment Forecaster...")

        # Create target if doesn't exist
        if "no_show" not in df.columns:
            no_shows = []
            for idx, row in df.iterrows():
                prob = 0.3
                if row.get("previous_no_shows", 0) > 0:
                    prob += 0.15
                if row.get("lead_time_days", 7) > 30:
                    prob += 0.1
                if row.get("distance_km", 5) > 15:
                    prob += 0.1
                if not row.get("reminder_sent", True):
                    prob += 0.1
                no_shows.append(np.random.random() < min(prob, 0.8))
            df = df.copy()
            df["no_show"] = no_shows

        y = df["no_show"].astype(int)

        # Prepare features
        df_copy = df.copy()

        # Encode categorical features
        appointment_type_map = {"routine": 0, "follow-up": 1, "specialist": 2, "emergency": 3}
        time_map = {"morning": 0, "afternoon": 1, "evening": 2}
        day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        insurance_map = {"Private": 0, "Government": 1, "None": 2}

        if "appointment_type" in df.columns:
            df_copy["appointment_type"] = df["appointment_type"].map(appointment_type_map).fillna(0)
        if "day_of_week" in df.columns:
            df_copy["day_of_week"] = df["day_of_week"].map(day_map).fillna(0)
        if "time_of_day" in df.columns:
            df_copy["time_of_day"] = df["time_of_day"].map(time_map).fillna(0)
        if "insurance_type" in df.columns:
            df_copy["insurance_type"] = df["insurance_type"].map(insurance_map).fillna(0)

        if "reminder_sent" in df.columns:
            df_copy["reminder_sent"] = df["reminder_sent"].astype(int)

        feature_cols = [
            "patient_age", "appointment_type", "day_of_week", "time_of_day",
            "lead_time_days", "previous_no_shows", "previous_appointments",
            "distance_km", "insurance_type", "reminder_sent"
        ]

        X = df_copy[[col for col in feature_cols if col in df_copy.columns]].fillna(0)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train Random Forest
        base_model = RandomForestClassifier(
            n_estimators=APPOINTMENT_FORECASTER_CONFIG["n_estimators"],
            max_depth=APPOINTMENT_FORECASTER_CONFIG["max_depth"],
            min_samples_split=APPOINTMENT_FORECASTER_CONFIG["min_samples_split"],
            random_state=APPOINTMENT_FORECASTER_CONFIG["random_state"],
            n_jobs=-1
        )

        # Calibrate probabilities
        self.model = CalibratedClassifierCV(base_model, method="sigmoid", cv=5)
        self.model.fit(X_train, y_train)

        # Evaluate
        train_accuracy = self.model.score(X_train, y_train)
        test_accuracy = self.model.score(X_test, y_test)
        print(f"Training accuracy: {train_accuracy:.4f}")
        print(f"Test accuracy: {test_accuracy:.4f}")

        self.is_trained = True

    def predict(self, raw_input: dict) -> dict:
        """
        Predict no-show probability.

        Args:
            raw_input: Dictionary with appointment data

        Returns:
            Dictionary with prediction and recommended actions
        """
        if not self.is_trained:
            return {
                "error": "Model not trained",
                "no_show_probability": 0,
                "risk_level": "Unknown",
                "recommended_overbooking_factor": 1.0,
                "suggested_actions": []
            }

        # Preprocess
        X = self.preprocess(raw_input)

        # Predict with calibrated probability
        no_show_prob = self.model.predict_proba(X)[0][1]

        # Determine risk level
        if no_show_prob < 0.3:
            risk_level = "Low"
        elif no_show_prob < 0.6:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # Calculate overbooking factor
        overbooking_factor = 1.0 + (no_show_prob * 0.5)  # Max 1.5x
        overbooking_factor = round(overbooking_factor, 1)

        # Generate suggested actions
        suggested_actions = []

        if no_show_prob > 0.3:
            suggested_actions.append("Send SMS reminder 48 hours before appointment")

        if no_show_prob > 0.5:
            suggested_actions.append("Call patient 24 hours before appointment")
            suggested_actions.append(f"Overbook slot with {int(overbooking_factor * 10 - 10)}% additional capacity")

        if no_show_prob > 0.7:
            suggested_actions.append("Consider requesting prepayment or deposit")
            suggested_actions.append("Assign backup patient from waitlist")

        # Add context-specific actions
        lead_time = raw_input.get("lead_time_days", 7)
        if lead_time > 30:
            suggested_actions.insert(0, "Send appointment confirmation email immediately")

        distance = raw_input.get("distance_km", 5)
        if distance > 20:
            suggested_actions.append("Offer telehealth alternative if applicable")

        previous_no_shows = raw_input.get("previous_no_shows", 0)
        if previous_no_shows > 2:
            suggested_actions.append("Flag patient for follow-up protocol")

        return {
            "no_show_probability": round(no_show_prob, 4),
            "risk_level": risk_level,
            "recommended_overbooking_factor": overbooking_factor,
            "suggested_actions": suggested_actions[:4]  # Top 4 actions
        }

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """
        Evaluate model on test set.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            return {"error": "Model not trained"}

        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    def save_model(self, path: str = None) -> None:
        """Save model to disk."""
        if path is None:
            path = str(APPOINTMENT_FORECASTER_MODEL)

        joblib.dump(self.model, path)
        print(f"Appointment forecaster saved to {path}")

    def load_model(self, path: str = None) -> None:
        """Load model from disk."""
        if path is None:
            path = str(APPOINTMENT_FORECASTER_MODEL)

        self.model = joblib.load(path)
        self.is_trained = True
        print(f"Appointment forecaster loaded from {path}")


if __name__ == "__main__":
    """Demo: Test appointment forecaster"""
    from utils.synthetic_data import generate_appointment_records

    print("Generating synthetic appointment data...")
    appointments_df = generate_appointment_records(500)

    forecaster = AppointmentForecaster()
    forecaster.train(appointments_df)

    test_input = {
        "patient_age": 45,
        "appointment_type": "follow-up",
        "day_of_week": "Monday",
        "time_of_day": "morning",
        "lead_time_days": 45,
        "previous_no_shows": 2,
        "previous_appointments": 8,
        "distance_km": 25,
        "insurance_type": "Government",
        "reminder_sent": False
    }

    print("\nMaking prediction...")
    result = forecaster.predict(test_input)
    print("\nNo-Show Prediction:")
    print(f"No-Show Probability: {result['no_show_probability']:.4f}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Overbooking Factor: {result['recommended_overbooking_factor']}")
    print(f"Suggested Actions:")
    for action in result['suggested_actions']:
        print(f"  - {action}")

    print("\nSaving model...")
    forecaster.save_model()
