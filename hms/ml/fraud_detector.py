"""
Billing Anomaly & Fraud Detector using Isolation Forest and Autoencoder.
Detects fraudulent billing patterns and anomalies.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, Any
import sys
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import FRAUD_DETECTOR_CONFIG, FRAUD_DETECTOR_IF_MODEL, FRAUD_DETECTOR_AE_MODEL

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False


class FraudDetector:
    """
    Ensemble fraud detection using Isolation Forest and Autoencoder.
    """

    def __init__(self):
        """Initialize fraud detector."""
        self.if_model = None
        self.ae_model = None
        self.scaler = StandardScaler()
        self.pca = None
        self.is_trained = False

    def preprocess(self, raw_input: dict) -> pd.DataFrame:
        """
        Preprocess billing data.

        Args:
            raw_input: Dictionary with billing features

        Returns:
            DataFrame with processed features
        """
        bill_amount = raw_input.get("bill_amount", 5000)
        service_codes = raw_input.get("service_codes", [])
        diagnosis_codes = raw_input.get("diagnosis_codes", [])
        num_services = raw_input.get("num_services", 1)
        length_of_stay_days = raw_input.get("length_of_stay_days", 3)
        patient_age = raw_input.get("patient_age", 50)
        department = raw_input.get("department", "General")
        historical_avg_bill = raw_input.get("historical_avg_bill", 5000)
        deviation_from_avg = raw_input.get("deviation_from_avg", 0)

        features_dict = {
            "bill_amount": [bill_amount],
            "num_services": [num_services],
            "num_diagnosis_codes": [len(diagnosis_codes) if isinstance(diagnosis_codes, list) else 1],
            "length_of_stay_days": [length_of_stay_days],
            "patient_age": [patient_age],
            "historical_avg_bill": [historical_avg_bill],
            "deviation_from_avg": [deviation_from_avg],
            "amount_per_service": [bill_amount / max(num_services, 1)],
            "amount_per_day": [bill_amount / max(length_of_stay_days, 1)],
        }

        # Department encoding
        dept_map = {"Cardiology": 0, "Neurology": 1, "General": 2, "Orthopedic": 3, "ICU": 4}
        features_dict["department_encoded"] = [dept_map.get(department, 2)]

        # Service diversity
        unique_services = len(set(service_codes)) if isinstance(service_codes, list) else 1
        features_dict["service_diversity"] = [unique_services]

        return pd.DataFrame(features_dict)

    def train(self, df: pd.DataFrame) -> None:
        """
        Train fraud detector on billing data.

        Args:
            df: Training DataFrame with billing records
        """
        print("Training Fraud Detector...")

        # Create fraud label if doesn't exist
        if "is_fraud" not in df.columns:
            fraud_indicators = []
            for idx, row in df.iterrows():
                score = 0
                if abs(row.get("deviation_from_avg", 0)) > 2:
                    score += 0.4
                if row.get("num_services", 1) > 5:
                    score += 0.3
                if row.get("bill_amount", 0) > row.get("historical_avg_bill", 5000) * 3:
                    score += 0.3
                fraud_indicators.append(score >= 0.5 or np.random.random() < 0.05)
            df = df.copy()
            df["is_fraud"] = fraud_indicators

        # Prepare features
        df_copy = df.copy()

        # Handle categorical features
        if "department" in df.columns:
            dept_map = {"Cardiology": 0, "Neurology": 1, "General": 2, "Orthopedic": 3, "ICU": 4}
            df_copy["department_encoded"] = df["department"].map(dept_map).fillna(2)

        # Process service codes
        if "service_codes" in df.columns:
            df_copy["num_service_codes"] = df["service_codes"].apply(
                lambda x: len(x.split(";")) if isinstance(x, str) else 1
            )

        # Process diagnosis codes
        if "diagnosis_codes" in df.columns:
            df_copy["num_diagnosis_codes"] = df["diagnosis_codes"].apply(
                lambda x: len(x.split(";")) if isinstance(x, str) else 1
            )

        feature_cols = [
            "bill_amount", "num_services", "num_diagnosis_codes",
            "length_of_stay_days", "patient_age", "historical_avg_bill",
            "deviation_from_avg", "department_encoded"
        ]

        X = df_copy[[col for col in feature_cols if col in df_copy.columns]].fillna(0)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.if_model = IsolationForest(
            n_estimators=FRAUD_DETECTOR_CONFIG["if_n_estimators"],
            contamination=FRAUD_DETECTOR_CONFIG["if_contamination"],
            random_state=42
        )
        self.if_model.fit(X_scaled)

        # Train Autoencoder if Keras available
        if KERAS_AVAILABLE:
            self._train_autoencoder(X_scaled)

        print("Fraud detector training complete")
        self.is_trained = True

    def _train_autoencoder(self, X_scaled: np.ndarray) -> None:
        """Train autoencoder for anomaly detection."""
        input_dim = X_scaled.shape[1]
        encoding_dim = FRAUD_DETECTOR_CONFIG["ae_encoding_dim"]

        # Build autoencoder
        self.ae_model = Sequential([
            Dense(input_dim, activation="relu", input_shape=(input_dim,)),
            Dropout(0.2),
            Dense(encoding_dim, activation="relu"),
            Dropout(0.2),
            Dense(input_dim, activation="relu")
        ])

        self.ae_model.compile(optimizer=Adam(), loss="mse")

        # Train
        self.ae_model.fit(
            X_scaled, X_scaled,
            epochs=FRAUD_DETECTOR_CONFIG["ae_epochs"],
            batch_size=FRAUD_DETECTOR_CONFIG["ae_batch_size"],
            verbose=0
        )
        print("Autoencoder trained successfully")

    def predict(self, raw_input: dict) -> dict:
        """
        Detect fraud in a billing record.

        Args:
            raw_input: Dictionary with billing data

        Returns:
            Dictionary with anomaly score, fraud flag, and explanation
        """
        if not self.is_trained:
            return {
                "error": "Model not trained",
                "anomaly_score": 0,
                "is_fraud": False,
                "fraud_type": "Unknown",
                "suspicious_services": [],
                "explanation": "Model not ready",
                "action": "Train model first"
            }

        # Preprocess
        X = self.preprocess(raw_input)
        X_scaled = self.scaler.transform(X)

        # Isolation Forest score
        if_score = -self.if_model.score_samples(X_scaled)[0]
        if_score = (if_score - if_score.min()) / (if_score.max() - if_score.min() + 1e-6)
        if_score = max(0, min(1, if_score))

        # Autoencoder score
        ae_score = 0
        if self.ae_model is not None:
            try:
                X_pred = self.ae_model.predict(X_scaled, verbose=0)
                reconstruction_error = np.mean(np.square(X_scaled - X_pred))
                ae_score = min(1, reconstruction_error / 0.5)
            except:
                ae_score = 0

        # Combine scores
        anomaly_score = (
            FRAUD_DETECTOR_CONFIG["if_weight"] * if_score +
            FRAUD_DETECTOR_CONFIG["ae_weight"] * ae_score
        )

        is_fraud = anomaly_score > FRAUD_DETECTOR_CONFIG["fraud_threshold"]

        # Determine fraud type
        fraud_types = []
        deviation = raw_input.get("deviation_from_avg", 0)
        if deviation > 2:
            fraud_types.append("Overcharging")
        if deviation < -0.5:
            fraud_types.append("Undercharging")

        num_services = raw_input.get("num_services", 1)
        if num_services > 5:
            fraud_types.append("Upcoding")

        bill_amount = raw_input.get("bill_amount", 0)
        historical_avg = raw_input.get("historical_avg_bill", 1)
        if bill_amount > historical_avg * 3:
            fraud_types.append("Billing for unnecessary services")

        fraud_type = fraud_types[0] if fraud_types else "Unusual pattern"

        # Identify suspicious services
        suspicious_services = []
        service_codes = raw_input.get("service_codes", [])
        if isinstance(service_codes, list) and num_services > 3:
            suspicious_services = service_codes[:int(num_services / 2)]

        # Generate explanation
        if is_fraud:
            explanation = f"Bill is {deviation:.1f}x the average for this diagnosis. Pattern suggests {fraud_type.lower()}."
        else:
            explanation = "Billing pattern is within normal range."

        action = "Flag for manual audit" if is_fraud else "Approved"

        return {
            "anomaly_score": round(anomaly_score, 4),
            "is_fraud": is_fraud,
            "fraud_type": fraud_type,
            "suspicious_services": suspicious_services[:3],
            "explanation": explanation,
            "action": action,
            "if_score": round(if_score, 4),
            "ae_score": round(ae_score, 4)
        }

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """
        Evaluate fraud detector.

        Args:
            X_test: Test features
            y_test: True labels

        Returns:
            Dictionary with evaluation metrics
        """
        if self.if_model is None:
            return {"error": "Model not trained"}

        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        X_scaled = self.scaler.transform(X_test)
        y_pred = self.if_model.predict(X_scaled)
        y_pred_binary = (y_pred == -1).astype(int)

        accuracy = accuracy_score(y_test, y_pred_binary)
        precision = precision_score(y_test, y_pred_binary, zero_division=0)
        recall = recall_score(y_test, y_pred_binary, zero_division=0)
        f1 = f1_score(y_test, y_pred_binary, zero_division=0)

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    def save_model(self, path: str = None) -> None:
        """Save models to disk."""
        if path is None:
            path = str(FRAUD_DETECTOR_IF_MODEL)

        model_data = {
            "if_model": self.if_model,
            "ae_model": self.ae_model,
            "scaler": self.scaler,
        }
        joblib.dump(model_data, path)
        print(f"Fraud detector saved to {path}")

    def load_model(self, path: str = None) -> None:
        """Load models from disk."""
        if path is None:
            path = str(FRAUD_DETECTOR_IF_MODEL)

        model_data = joblib.load(path)
        self.if_model = model_data["if_model"]
        self.ae_model = model_data["ae_model"]
        self.scaler = model_data["scaler"]
        self.is_trained = True
        print(f"Fraud detector loaded from {path}")


if __name__ == "__main__":
    """Demo: Test fraud detector"""
    from utils.synthetic_data import generate_billing_records

    print("Generating synthetic billing data...")
    billing_df = generate_billing_records(500)

    detector = FraudDetector()
    detector.train(billing_df)

    # Test cases
    test_cases = [
        {
            "bill_amount": 45000,
            "service_codes": ["MRI", "CT_SCAN", "MRI", "LAB_WORK", "MRI"],
            "diagnosis_codes": ["DIAB"],
            "num_services": 5,
            "length_of_stay_days": 2,
            "patient_age": 60,
            "department": "Cardiology",
            "historical_avg_bill": 8000,
            "deviation_from_avg": 4.6,
        },
        {
            "bill_amount": 8500,
            "service_codes": ["CONSULTATION", "LAB_WORK"],
            "diagnosis_codes": ["HTN"],
            "num_services": 2,
            "length_of_stay_days": 1,
            "patient_age": 55,
            "department": "General",
            "historical_avg_bill": 7500,
            "deviation_from_avg": 0.13,
        }
    ]

    print("\nTesting fraud detection:")
    for i, test_input in enumerate(test_cases, 1):
        result = detector.predict(test_input)
        print(f"\nTest Case {i}:")
        print(f"  Anomaly Score: {result['anomaly_score']:.4f}")
        print(f"  Is Fraud: {result['is_fraud']}")
        print(f"  Fraud Type: {result['fraud_type']}")
        print(f"  Action: {result['action']}")

    print("\nSaving model...")
    detector.save_model()
