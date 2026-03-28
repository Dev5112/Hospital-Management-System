"""
Disease/Diagnosis Predictor using XGBoost.
Predicts diseases based on symptoms, vitals, and patient characteristics.
"""

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
import shap
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from typing import Dict, List, Any
import sys
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import DISEASE_PREDICTOR_MODEL, DISEASE_PREDICTOR_CONFIG
from utils.preprocessing import normalize_vital_signs


class DiseasePredictor:
    """
    XGBoost-based disease prediction model with SHAP explainability.
    """

    def __init__(self):
        """Initialize the disease predictor."""
        self.model = None
        self.symptom_vectorizer = None
        self.label_encoder = None
        self.feature_names = None
        self.shap_explainer = None
        self.diseases = DISEASE_PREDICTOR_CONFIG["diseases"]
        self.is_trained = False

    def preprocess(self, raw_input: dict) -> pd.DataFrame:
        """
        Preprocess raw input into features.

        Args:
            raw_input: Dictionary with patient data

        Returns:
            DataFrame with processed features
        """
        # Extract features
        age = raw_input.get("age", 40)
        gender = raw_input.get("gender", "M")
        bp_systolic = raw_input.get("blood_pressure", 130)
        temperature = raw_input.get("temperature", 37.0)
        heart_rate = raw_input.get("heart_rate", 72)
        blood_glucose = raw_input.get("blood_glucose", 100)
        bmi = raw_input.get("bmi", 24)
        symptoms = raw_input.get("symptoms", [])
        lab_results = raw_input.get("lab_results", {})

        # Convert symptoms to string for TF-IDF
        if isinstance(symptoms, list):
            symptoms_str = " ".join(symptoms)
        else:
            symptoms_str = str(symptoms)

        # Create base features DataFrame
        features_dict = {
            "age": [age],
            "gender_encoded": [1 if gender.upper() == "M" else 0],
            "systolic_bp": [bp_systolic],
            "temperature": [temperature],
            "heart_rate": [heart_rate],
            "blood_glucose": [blood_glucose],
            "bmi": [bmi],
        }

        # Add lab results as features
        for lab_name, lab_value in lab_results.items():
            features_dict[f"lab_{lab_name}"] = [lab_value]

        # Create base DataFrame
        X = pd.DataFrame(features_dict)

        # Process symptoms with TF-IDF
        if self.symptom_vectorizer is not None:
            symptom_features = self.symptom_vectorizer.transform([symptoms_str])
            symptom_df = pd.DataFrame(
                symptom_features.toarray(),
                columns=[f"symptom_{i}" for i in range(symptom_features.shape[1])]
            )
            X = pd.concat([X, symptom_df], axis=1)

        return X

    def train(self, df: pd.DataFrame) -> None:
        """
        Train the disease predictor on synthetic data.

        Args:
            df: Training DataFrame with all features and diagnosis
        """
        print("Training Disease Predictor...")

        # Create diagnosis column if it doesn't exist (simulate for demo)
        if "diagnosis" not in df.columns:
            # Generate synthetic diagnoses based on patterns
            diagnoses = []
            for idx, row in df.iterrows():
                if row["blood_glucose"] > 125 and row["age"] > 40:
                    diagnoses.append("Type 2 Diabetes")
                elif row["systolic_bp"] > 140:
                    diagnoses.append("Hypertension")
                elif row["temperature"] > 38.5:
                    diagnoses.append("Pneumonia")
                else:
                    diagnoses.append(np.random.choice(self.diseases))
            df = df.copy()
            df["diagnosis"] = diagnoses

        # Prepare target
        self.label_encoder = LabelEncoder()
        df_copy = df.copy()
        df_copy.loc[:, "diagnosis"] = df_copy["diagnosis"].fillna("Unknown")
        y = self.label_encoder.fit_transform(df_copy["diagnosis"])

        # Process symptoms
        if "symptoms" in df.columns:
            self.symptom_vectorizer = TfidfVectorizer(
                max_features=DISEASE_PREDICTOR_CONFIG["symptoms_max_features"],
                lowercase=True
            )
            symptoms_str = df["symptoms"].fillna("none").astype(str)
            symptom_features = self.symptom_vectorizer.fit_transform(symptoms_str)
            symptom_df = pd.DataFrame(
                symptom_features.toarray(),
                columns=[f"symptom_{i}" for i in range(symptom_features.shape[1])]
            )
        else:
            symptom_df = pd.DataFrame()

        # Select numerical features
        numerical_cols = ["age", "systolic_bp", "temperature", "heart_rate", "blood_glucose", "bmi"]
        numerical_features = df[[col for col in numerical_cols if col in df.columns]]

        # Encode gender if present
        if "gender" in df.columns:
            gender_encoded = pd.DataFrame({
                "gender_encoded": (df["gender"] == "M").astype(int)
            })
        else:
            gender_encoded = pd.DataFrame()

        # Combine all features
        X = pd.concat([numerical_features, gender_encoded, symptom_df], axis=1)
        X = X.fillna(0)

        self.feature_names = X.columns.tolist()

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=DISEASE_PREDICTOR_CONFIG["n_estimators"],
            max_depth=DISEASE_PREDICTOR_CONFIG["max_depth"],
            learning_rate=DISEASE_PREDICTOR_CONFIG["learning_rate"],
            random_state=DISEASE_PREDICTOR_CONFIG["random_state"],
            objective="multi:softprob",
            tree_method="hist",
            device="cpu"
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        # Create SHAP explainer
        self.shap_explainer = shap.TreeExplainer(self.model)

        # Evaluate
        train_accuracy = self.model.score(X_train, y_train)
        test_accuracy = self.model.score(X_test, y_test)
        print(f"Training accuracy: {train_accuracy:.4f}")
        print(f"Test accuracy: {test_accuracy:.4f}")

        self.is_trained = True

    def predict(self, raw_input: dict) -> dict:
        """
        Predict disease for a patient.

        Args:
            raw_input: Dictionary with patient data

        Returns:
            Dictionary with predictions, explanations, and confidence
        """
        if not self.is_trained:
            return {
                "error": "Model not trained",
                "top_predictions": [],
                "shap_explanation": {},
                "confidence": "low"
            }

        # Preprocess input
        X = self.preprocess(raw_input)

        # Handle feature mismatch
        if len(X.columns) < len(self.feature_names):
            for missing_col in self.feature_names:
                if missing_col not in X.columns:
                    X[missing_col] = 0

        X = X[[col for col in self.feature_names if col in X.columns]]

        # Make prediction
        y_pred_proba = self.model.predict_proba(X)[0]
        top_indices = np.argsort(y_pred_proba)[::-1][:3]

        top_predictions = []
        for idx in top_indices:
            disease = self.label_encoder.classes_[idx]
            probability = float(y_pred_proba[idx])
            top_predictions.append({
                "condition": disease,
                "probability": round(probability, 4)
            })

        # SHAP explanation
        shap_values = self.shap_explainer.shap_values(X)
        if isinstance(shap_values, list):
            shap_values = shap_values[top_indices[0]]
        else:
            shap_values = shap_values[0]

        feature_importance = {}
        for i, feature in enumerate(self.feature_names):
            if i < len(shap_values):
                feature_importance[feature] = round(float(np.abs(shap_values[i])), 4)

        # Sort and keep top 10
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])

        # Confidence level
        max_prob = top_predictions[0]["probability"]
        if max_prob > 0.7:
            confidence = "high"
        elif max_prob > 0.5:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "top_predictions": top_predictions,
            "shap_explanation": feature_importance,
            "confidence": confidence,
            "max_probability": round(max_prob, 4)
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
        precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    def save_model(self, path: str = None) -> None:
        """
        Save model to disk.

        Args:
            path: Path to save model
        """
        if path is None:
            path = str(DISEASE_PREDICTOR_MODEL)

        model_data = {
            "model": self.model,
            "symptoms_vectorizer": self.symptom_vectorizer,
            "label_encoder": self.label_encoder,
            "feature_names": self.feature_names,
        }

        joblib.dump(model_data, path)
        print(f"Disease predictor saved to {path}")

    def load_model(self, path: str = None) -> None:
        """
        Load model from disk.

        Args:
            path: Path to load model from
        """
        if path is None:
            path = str(DISEASE_PREDICTOR_MODEL)

        model_data = joblib.load(path)
        self.model = model_data["model"]
        self.symptom_vectorizer = model_data["symptoms_vectorizer"]
        self.label_encoder = model_data["label_encoder"]
        self.feature_names = model_data["feature_names"]
        self.shap_explainer = shap.TreeExplainer(self.model)
        self.is_trained = True
        print(f"Disease predictor loaded from {path}")


if __name__ == "__main__":
    """Demo: Test disease predictor"""
    from utils.synthetic_data import generate_patient_records

    # Generate synthetic data
    print("Generating synthetic patient data...")
    patients_df = generate_patient_records(500)

    # Initialize and train
    predictor = DiseasePredictor()
    predictor.train(patients_df)

    # Test prediction
    test_input = {
        "age": 55,
        "gender": "M",
        "blood_pressure": 160,
        "temperature": 37.5,
        "heart_rate": 85,
        "blood_glucose": 180,
        "bmi": 28,
        "symptoms": ["fever", "fatigue", "increased_thirst"],
        "lab_results": {"WBC": 12.5, "RBC": 4.2}
    }

    print("\nMaking prediction...")
    result = predictor.predict(test_input)
    print("\nPrediction Result:")
    print(f"Top predictions: {result['top_predictions']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Feature importance (SHAP): {result['shap_explanation']}")

    # Save model
    print("\nSaving model...")
    predictor.save_model()
