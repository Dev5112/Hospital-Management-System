"""
Unified ML Model Training Pipeline.
Trains, evaluates, and saves all ML models.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import MODEL_TRAINER_CONFIG, MODELS_DIR, LOGS_DIR
from utils.synthetic_data import (
    generate_patient_records,
    generate_appointment_records,
    generate_billing_records,
    generate_admission_records,
    generate_drug_pairs,
    generate_time_series_occupancy
)
from ml.disease_predictor import DiseasePredictor
from ml.readmission_risk import ReadmissionRiskPredictor
from ml.bed_optimizer import BedOptimizer
from ml.appointment_forecaster import AppointmentForecaster
from ml.fraud_detector import FraudDetector
from ml.drug_interaction import DrugInteractionScorer


class ModelTrainer:
    """Unified training pipeline for all HMS models."""

    def __init__(self):
        """Initialize model trainer."""
        self.training_log = []
        self.logs_dir = Path(LOGS_DIR)
        self.logs_dir.mkdir(exist_ok=True)

    def log_training(self, model_name: str, status: str, metrics: dict = None) -> None:
        """Log training results."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "status": status,
            "metrics": metrics or {}
        }
        self.training_log.append(entry)
        print(f"[LOG] {model_name}: {status}")

    def save_training_log(self) -> None:
        """Save training log to file."""
        log_file = MODEL_TRAINER_CONFIG["log_file"]
        with open(log_file, "w") as f:
            json.dump(self.training_log, f, indent=4)
        print(f"\nTraining log saved to {log_file}")

    def train_disease_predictor(self) -> None:
        """Train disease predictor model."""
        print("\n" + "="*60)
        print("Training Disease Predictor")
        print("="*60)

        try:
            print("Generating patient data...")
            patients_df = generate_patient_records(1000)

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
                "symptoms": ["fever", "fatigue"],
                "lab_results": {"WBC": 12.5}
            }

            result = predictor.predict(test_input)
            predictor.save_model()

            self.log_training(
                "DiseasePredictor",
                "SUCCESS",
                {"top_prediction": result["top_predictions"][0]["condition"]} if result.get("top_predictions") else {}
            )
        except Exception as e:
            self.log_training("DiseasePredictor", f"FAILED: {str(e)}")
            print(f"Error: {e}")

    def train_readmission_risk(self) -> None:
        """Train readmission risk predictor."""
        print("\n" + "="*60)
        print("Training Readmission Risk Predictor")
        print("="*60)

        try:
            print("Generating admission data...")
            admissions_df = generate_admission_records(1000)

            predictor = ReadmissionRiskPredictor()
            predictor.train(admissions_df)

            # Test prediction
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

            result = predictor.predict(test_input)
            predictor.save_model()

            self.log_training(
                "ReadmissionRiskPredictor",
                "SUCCESS",
                {"risk_category": result.get("risk_category")}
            )
        except Exception as e:
            self.log_training("ReadmissionRiskPredictor", f"FAILED: {str(e)}")
            print(f"Error: {e}")

    def train_bed_optimizer(self) -> None:
        """Train bed optimizer model."""
        print("\n" + "="*60)
        print("Training Bed Optimizer")
        print("="*60)

        try:
            print("Generating occupancy data...")
            occupancy_df = generate_time_series_occupancy(365)

            optimizer = BedOptimizer()
            optimizer.train(occupancy_df)

            # Test forecast
            icu_data = occupancy_df[occupancy_df["ward_type"] == "ICU"]
            test_input = {
                "ward_type": "ICU",
                "historical_occupancy": icu_data["occupancy"].tail(90).values.tolist(),
                "forecast_days": 7
            }

            result = optimizer.predict(test_input)
            optimizer.save_model()

            self.log_training(
                "BedOptimizer",
                "SUCCESS",
                {"overflow_risk": result.get("overflow_risk")}
            )
        except Exception as e:
            self.log_training("BedOptimizer", f"FAILED: {str(e)}")
            print(f"Error: {e}")

    def train_appointment_forecaster(self) -> None:
        """Train appointment forecaster model."""
        print("\n" + "="*60)
        print("Training Appointment Forecaster")
        print("="*60)

        try:
            print("Generating appointment data...")
            appointments_df = generate_appointment_records(1000)

            forecaster = AppointmentForecaster()
            forecaster.train(appointments_df)

            # Test prediction
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

            result = forecaster.predict(test_input)
            forecaster.save_model()

            self.log_training(
                "AppointmentForecaster",
                "SUCCESS",
                {"risk_level": result.get("risk_level")}
            )
        except Exception as e:
            self.log_training("AppointmentForecaster", f"FAILED: {str(e)}")
            print(f"Error: {e}")

    def train_fraud_detector(self) -> None:
        """Train fraud detector model."""
        print("\n" + "="*60)
        print("Training Fraud Detector")
        print("="*60)

        try:
            print("Generating billing data...")
            billing_df = generate_billing_records(1000)

            detector = FraudDetector()
            detector.train(billing_df)

            # Test prediction
            test_input = {
                "bill_amount": 45000,
                "service_codes": ["MRI", "CT_SCAN", "MRI"],
                "diagnosis_codes": ["DIAB"],
                "num_services": 3,
                "length_of_stay_days": 2,
                "patient_age": 60,
                "department": "Cardiology",
                "historical_avg_bill": 8000,
                "deviation_from_avg": 4.6,
            }

            result = detector.predict(test_input)
            detector.save_model()

            self.log_training(
                "FraudDetector",
                "SUCCESS",
                {"is_fraud": result.get("is_fraud")}
            )
        except Exception as e:
            self.log_training("FraudDetector", f"FAILED: {str(e)}")
            print(f"Error: {e}")

    def train_drug_interaction(self) -> None:
        """Train drug interaction scorer."""
        print("\n" + "="*60)
        print("Training Drug Interaction Scorer")
        print("="*60)

        try:
            print("Generating drug pair data...")
            drugs_df = generate_drug_pairs(500)

            scorer = DrugInteractionScorer()
            scorer.train(drugs_df)

            # Test prediction
            test_input = {
                "medications": ["Warfarin", "Aspirin", "Metformin"]
            }

            result = scorer.predict(test_input)
            scorer.save_model()

            self.log_training(
                "DrugInteractionScorer",
                "SUCCESS",
                {"total_risk_score": result.get("total_risk_score")}
            )
        except Exception as e:
            self.log_training("DrugInteractionScorer", f"FAILED: {str(e)}")
            print(f"Error: {e}")

    def train_all(self) -> None:
        """Train all models."""
        print("Starting Complete Training Pipeline...")
        print(f"Models directory: {MODELS_DIR}")

        self.train_disease_predictor()
        self.train_readmission_risk()
        self.train_bed_optimizer()
        self.train_appointment_forecaster()
        self.train_fraud_detector()
        self.train_drug_interaction()

        self.save_training_log()
        print("\n" + "="*60)
        print("Training Pipeline Complete!")
        print("="*60)

    def train_model(self, model_name: str) -> None:
        """Train a specific model."""
        model_methods = {
            "disease": self.train_disease_predictor,
            "readmission": self.train_readmission_risk,
            "bed": self.train_bed_optimizer,
            "appointment": self.train_appointment_forecaster,
            "fraud": self.train_fraud_detector,
            "drug": self.train_drug_interaction,
        }

        if model_name in model_methods:
            model_methods[model_name]()
            self.save_training_log()
        else:
            print(f"Unknown model: {model_name}")
            print(f"Available models: {', '.join(model_methods.keys())}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="HMS ML Model Training Pipeline")
    parser.add_argument(
        "--train-all",
        action="store_true",
        help="Train all models"
    )
    parser.add_argument(
        "--train",
        type=str,
        help="Train specific model (disease, readmission, bed, appointment, fraud, drug)"
    )
    parser.add_argument(
        "--evaluate-all",
        action="store_true",
        help="Evaluate all trained models"
    )

    args = parser.parse_args()

    trainer = ModelTrainer()

    if args.train_all:
        trainer.train_all()
    elif args.train:
        trainer.train_model(args.train)
    elif args.evaluate_all:
        print("Model evaluation not yet implemented in this version.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
