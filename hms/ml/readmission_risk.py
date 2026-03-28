"""
Patient Readmission Risk Predictor using ensemble methods.
Predicts risk of hospital readmission within 30 days.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List, Any
import sys
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import READMISSION_RISK_MODEL, READMISSION_RISK_CONFIG


class ReadmissionRiskPredictor:
    """
    Ensemble readmission risk predictor combining Gradient Boosting and Logistic Regression.
    """

    def __init__(self):
        """Initialize the readmission risk predictor."""
        self.model = None
        self.comorbidity_encoder = {}
        self.diagnosis_encoder = None
        self.discharge_encoder = None
        self.insurance_encoder = None
        self.is_trained = False

    def preprocess(self, raw_input: dict) -> pd.DataFrame:
        """
        Preprocess raw input into features.

        Args:
            raw_input: Dictionary with patient data

        Returns:
            DataFrame with processed features
        """
        age = raw_input.get("age", 60)
        gender = raw_input.get("gender", "M")
        diagnosis = raw_input.get("diagnosis", "Unknown")
        num_previous_admissions = raw_input.get("num_previous_admissions", 0)
        length_of_stay_days = raw_input.get("length_of_stay_days", 3)
        comorbidities = raw_input.get("comorbidities", [])
        medication_count = raw_input.get("medication_count", 0)
        medication_adherence_score = raw_input.get("medication_adherence_score", 0.5)
        discharge_disposition = raw_input.get("discharge_disposition", "home")
        insurance_type = raw_input.get("insurance_type", "Private")

        # Convert comorbidities to string if list
        if isinstance(comorbidities, list):
            comorbidities_str = ";".join(comorbidities)
        else:
            comorbidities_str = str(comorbidities)

        features_dict = {
            "age": [age],
            "gender_encoded": [1 if gender.upper() == "M" else 0],
            "num_previous_admissions": [num_previous_admissions],
            "length_of_stay_days": [length_of_stay_days],
            "medication_count": [medication_count],
            "medication_adherence_score": [medication_adherence_score],
        }

        # Add comorbidity features
        comorbidities_list = comorbidities_str.split(";") if comorbidities_str != "none" else []
        for comorb in ["Hypertension", "Diabetes", "COPD", "CKD"]:
            features_dict[f"has_{comorb.lower()}"] = [1 if comorb in comorbidities_list else 0]

        # Diagnosis encoding
        if hasattr(self, "diagnosis_encoder") and self.diagnosis_encoder:
            try:
                diagnosis_encoded = self.diagnosis_encoder.transform([diagnosis])[0]
            except:
                diagnosis_encoded = 0
        else:
            diagnosis_encoded = 0
        features_dict["diagnosis_encoded"] = [diagnosis_encoded]

        # Discharge disposition encoding
        discharge_map = {"home": 0, "facility": 1, "AMA": 2}
        features_dict["discharge_disposition_encoded"] = [discharge_map.get(discharge_disposition, 0)]

        # Insurance encoding
        insurance_map = {"Private": 0, "Government": 1, "None": 2}
        features_dict["insurance_encoded"] = [insurance_map.get(insurance_type, 0)]

        return pd.DataFrame(features_dict)

    def train(self, df: pd.DataFrame) -> None:
        """
        Train the readmission risk predictor.

        Args:
            df: Training DataFrame
        """
        print("Training Readmission Risk Predictor...")

        # Create target if doesn't exist
        if "readmission_within_30_days" not in df.columns:
            readmissions = []
            for idx, row in df.iterrows():
                risk_score = 0
                if row.get("num_previous_admissions", 0) > 2:
                    risk_score += 30
                if row.get("medication_adherence_score", 0.5) < 0.5:
                    risk_score += 25
                if ";" in str(row.get("comorbidities", "")):
                    risk_score += 20
                if row.get("discharge_disposition", "home") != "home":
                    risk_score += 15
                if row.get("age", 40) > 70:
                    risk_score += 20

                readmissions.append(np.random.random() < (risk_score / 100))
            df = df.copy()
            df["readmission_within_30_days"] = readmissions

        y = df["readmission_within_30_days"].astype(int)

        # Prepare features
        df_copy = df.copy()

        # Encode diagnosis
        if "diagnosis" in df.columns:
            self.diagnosis_encoder = LabelEncoder()
            df_copy["diagnosis"] = df_copy["diagnosis"].fillna("Unknown")
            df_copy["diagnosis_encoded"] = self.diagnosis_encoder.fit_transform(df_copy["diagnosis"])
        else:
            df_copy["diagnosis_encoded"] = 0

        # Encode comorbidities (binary flags)
        comorbidities_list = set()
        for comorbs in df.get("comorbidities", []):
            if isinstance(comorbs, str):
                comorbidities_list.update(c.strip() for c in comorbs.split(";") if c.lower() != "none")

        for comorb in ["Hypertension", "Diabetes", "COPD", "CKD"]:
            df_copy[f"has_{comorb.lower()}"] = 0

        for idx, comorbidities_str in enumerate(df.get("comorbidities", [])):
            if isinstance(comorbidities_str, str) and comorbidities_str != "none":
                for comorb in ["Hypertension", "Diabetes", "COPD", "CKD"]:
                    if comorb in comorbidities_str:
                        df_copy.at[idx, f"has_{comorb.lower()}"] = 1

        # Select features
        feature_cols = [
            "age", "num_previous_admissions", "length_of_stay_days",
            "medication_count", "medication_adherence_score",
            "diagnosis_encoded", "has_hypertension", "has_diabetes",
            "has_copd", "has_ckd"
        ]

        # Add gender if available
        if "gender" in df.columns:
            df_copy["gender_encoded"] = (df["gender"] == "M").astype(int)
            feature_cols.insert(0, "gender_encoded")

        # Add discharge disposition if available
        if "discharge_disposition" in df.columns:
            discharge_map = {"home": 0, "facility": 1, "AMA": 2}
            df_copy["discharge_disposition_encoded"] = df["discharge_disposition"].map(discharge_map).fillna(0)
            feature_cols.append("discharge_disposition_encoded")

        # Add insurance if available
        if "insurance_type" in df.columns:
            insurance_map = {"Private": 0, "Government": 1, "None": 2}
            df_copy["insurance_encoded"] = df["insurance_type"].map(insurance_map).fillna(0)
            feature_cols.append("insurance_encoded")

        X = df_copy[[col for col in feature_cols if col in df_copy.columns]].fillna(0)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Create ensemble model
        gb_model = GradientBoostingClassifier(
            n_estimators=READMISSION_RISK_CONFIG["gb_n_estimators"],
            learning_rate=READMISSION_RISK_CONFIG["gb_learning_rate"],
            random_state=READMISSION_RISK_CONFIG["random_state"]
        )

        lr_model = LogisticRegression(random_state=READMISSION_RISK_CONFIG["random_state"])

        self.model = VotingClassifier(
            estimators=[("gb", gb_model), ("lr", lr_model)],
            voting="soft"
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        train_accuracy = self.model.score(X_train, y_train)
        test_accuracy = self.model.score(X_test, y_test)
        print(f"Training accuracy: {train_accuracy:.4f}")
        print(f"Test accuracy: {test_accuracy:.4f}")

        self.is_trained = True

    def predict(self, raw_input: dict) -> dict:
        """
        Predict readmission risk.

        Args:
            raw_input: Dictionary with patient data

        Returns:
            Dictionary with risk score, category, probability, and recommendations
        """
        if not self.is_trained:
            return {
                "error": "Model not trained",
                "risk_score": 0,
                "risk_category": "Unknown",
                "readmission_probability": 0,
                "top_risk_factors": [],
                "recommendation": "Model not ready"
            }

        # Preprocess
        X = self.preprocess(raw_input)

        # Predict
        risk_prob = self.model.predict_proba(X)[0][1]
        risk_score = int(risk_prob * 100)

        # Determine risk category
        risk_thresholds = READMISSION_RISK_CONFIG["risk_thresholds"]
        risk_category = "Unknown"
        for category, (min_val, max_val) in risk_thresholds.items():
            if min_val <= risk_score < max_val:
                risk_category = category
                break

        # Identify top risk factors
        top_risk_factors = []
        age = raw_input.get("age", 60)
        num_prev_admissions = raw_input.get("num_previous_admissions", 0)
        medication_adherence = raw_input.get("medication_adherence_score", 0.5)
        comorbidities = raw_input.get("comorbidities", [])
        discharge_disposition = raw_input.get("discharge_disposition", "home")

        if num_prev_admissions > 2:
            top_risk_factors.append(f"{num_prev_admissions} previous admissions in 6 months")
        if medication_adherence < 0.5:
            top_risk_factors.append(f"Low medication adherence ({medication_adherence:.1f})")
        if isinstance(comorbidities, list) and len(comorbidities) > 1:
            top_risk_factors.append(f"Multiple comorbidities ({len(comorbidities)})")
        if discharge_disposition != "home":
            top_risk_factors.append(f"Discharge to {discharge_disposition} facility")
        if age > 70:
            top_risk_factors.append(f"Advanced age ({age} years)")

        # Generate recommendation
        if risk_category == "Low":
            recommendation = "Standard follow-up care, routine monitoring"
        elif risk_category == "Medium":
            recommendation = "Schedule follow-up within 14 days, monitor compliance"
        elif risk_category == "High":
            recommendation = "Schedule follow-up within 7 days, intensive case management"
        else:  # Critical
            recommendation = "Urgent intervention required, daily contact for 7 days"

        return {
            "risk_score": risk_score,
            "risk_category": risk_category,
            "readmission_probability": round(risk_prob, 4),
            "top_risk_factors": top_risk_factors[:3],
            "recommendation": recommendation
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
            path = str(READMISSION_RISK_MODEL)

        model_data = {
            "model": self.model,
            "diagnosis_encoder": self.diagnosis_encoder,
        }
        joblib.dump(model_data, path)
        print(f"Readmission risk predictor saved to {path}")

    def load_model(self, path: str = None) -> None:
        """Load model from disk."""
        if path is None:
            path = str(READMISSION_RISK_MODEL)

        model_data = joblib.load(path)
        self.model = model_data["model"]
        self.diagnosis_encoder = model_data["diagnosis_encoder"]
        self.is_trained = True
        print(f"Readmission risk predictor loaded from {path}")


if __name__ == "__main__":
    """Demo: Test readmission risk predictor"""
    from utils.synthetic_data import generate_admission_records

    print("Generating synthetic admission data...")
    admissions_df = generate_admission_records(500)

    predictor = ReadmissionRiskPredictor()
    predictor.train(admissions_df)

    test_input = {
        "age": 72,
        "gender": "M",
        "diagnosis": "Type 2 Diabetes",
        "num_previous_admissions": 3,
        "length_of_stay_days": 5,
        "comorbidities": ["Hypertension", "Diabetes"],
        "medication_count": 8,
        "medication_adherence_score": 0.4,
        "discharge_disposition": "home",
        "insurance_type": "Government"
    }

    print("\nMaking prediction...")
    result = predictor.predict(test_input)
    print("\nReadmission Risk Prediction:")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Risk Category: {result['risk_category']}")
    print(f"Readmission Probability: {result['readmission_probability']:.4f}")
    print(f"Top Risk Factors: {result['top_risk_factors']}")
    print(f"Recommendation: {result['recommendation']}")

    print("\nSaving model...")
    predictor.save_model()
