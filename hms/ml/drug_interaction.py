"""
Drug Interaction Risk Scorer using TF-IDF and classification.
Detects and classifies medication interactions.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from typing import Dict, List, Any
import sys
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import DRUG_INTERACTION_MODEL, DRUG_INTERACTION_CONFIG, DRUG_INTERACTION_DATA


class DrugInteractionScorer:
    """
    Drug interaction detection using TF-IDF similarity and classification.
    """

    def __init__(self):
        """Initialize drug interaction scorer."""
        self.tfidf_vectorizer = None
        self.interaction_classifier = None
        self.interaction_database = None
        self.drug_names = None
        self.is_trained = False

    def preprocess(self, raw_input: dict) -> Dict[str, Any]:
        """
        Preprocess medication list.

        Args:
            raw_input: Dictionary with medications list

        Returns:
            Processed data dictionary
        """
        medications = raw_input.get("medications", [])

        # Normalize drug names
        normalized_meds = [med.lower().strip() for med in medications]

        return {
            "medications": medications,
            "normalized_medications": normalized_meds,
            "num_medications": len(medications)
        }

    def train(self, df: pd.DataFrame) -> None:
        """
        Train drug interaction scorer.

        Args:
            df: DataFrame with drug pair data
        """
        print("Training Drug Interaction Scorer...")

        # Store drug interaction database
        self.interaction_database = df.copy()

        # Get unique drugs
        all_drugs = set(df["drug1"].unique()) | set(df["drug2"].unique())
        self.drug_names = sorted(list(all_drugs))

        # Vectorize drug names for similarity matching
        self.tfidf_vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 3),
            max_features=DRUG_INTERACTION_CONFIG["tfidf_max_features"]
        )

        self.tfidf_vectorizer.fit(self.drug_names)

        # Prepare training data for interaction classifier
        X_data = []
        y_data = []

        for idx, row in df.iterrows():
            drug1_vec = self.tfidf_vectorizer.transform([row["drug1"]]).toarray()[0]
            drug2_vec = self.tfidf_vectorizer.transform([row["drug2"]]).toarray()[0]

            # Combine features
            combined = np.concatenate([drug1_vec, drug2_vec])
            X_data.append(combined)
            y_data.append(1 if row["interacts"] else 0)

        if len(X_data) > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X_data, y_data, test_size=0.2, random_state=42
            )

            self.interaction_classifier = RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )
            self.interaction_classifier.fit(X_train, y_train)

        print("Drug interaction scorer training complete")
        self.is_trained = True

    def _find_drug_match(self, input_drug: str) -> str:
        """
        Find closest matching drug name using TF-IDF similarity.

        Args:
            input_drug: Drug name to match

        Returns:
            Best matching drug name
        """
        input_drug_lower = input_drug.lower().strip()

        # Exact match
        for db_drug in self.drug_names:
            if db_drug.lower() == input_drug_lower:
                return db_drug

        # Similarity match
        input_vec = self.tfidf_vectorizer.transform([input_drug_lower]).toarray()
        db_vecs = self.tfidf_vectorizer.transform(self.drug_names).toarray()
        similarities = cosine_similarity(input_vec, db_vecs)[0]

        best_idx = np.argmax(similarities)
        if similarities[best_idx] >= DRUG_INTERACTION_CONFIG["similarity_threshold"]:
            return self.drug_names[best_idx]

        return None

    def predict(self, raw_input: dict) -> dict:
        """
        Check drug interactions.

        Args:
            raw_input: Dictionary with medications list

        Returns:
            Dictionary with interactions, risk score, and recommendations
        """
        if not self.is_trained or self.interaction_database is None:
            return {
                "error": "Model not trained",
                "interactions_found": [],
                "total_risk_score": 0,
                "safe_to_prescribe": True,
                "alternatives": []
            }

        processed = self.preprocess(raw_input)
        medications = processed["medications"]

        if len(medications) < 2:
            return {
                "interactions_found": [],
                "total_risk_score": 0,
                "safe_to_prescribe": True,
                "alternatives": []
            }

        interactions_found = []
        total_risk_score = 0
        safe_to_prescribe = True

        # Check all drug pairs
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                drug1 = medications[i]
                drug2 = medications[j]

                # Find matches in database
                match1 = self._find_drug_match(drug1)
                match2 = self._find_drug_match(drug2)

                if match1 is None or match2 is None:
                    continue

                # Check database
                db_result = self.interaction_database[
                    ((self.interaction_database["drug1"] == match1) &
                     (self.interaction_database["drug2"] == match2)) |
                    ((self.interaction_database["drug1"] == match2) &
                     (self.interaction_database["drug2"] == match1))
                ]

                if len(db_result) > 0:
                    db_row = db_result.iloc[0]
                    if db_row["interacts"]:
                        severity = db_row.get("severity", "Moderate")
                        effect = db_row.get("effect", "Unknown")

                        interactions_found.append({
                            "drug_pair": [drug1, drug2],
                            "severity": severity,
                            "effect": effect,
                            "recommendation": self._get_recommendation(severity)
                        })

                        # Add to risk score
                        severity_scores = {"Mild": 5, "Moderate": 25, "Severe": 50}
                        total_risk_score += severity_scores.get(severity, 15)

                        if severity == "Severe":
                            safe_to_prescribe = False

        # Generate alternatives
        alternatives = self._generate_alternatives(medications, interactions_found)

        return {
            "interactions_found": interactions_found[:5],
            "total_risk_score": min(100, total_risk_score),
            "safe_to_prescribe": safe_to_prescribe,
            "alternatives": alternatives[:3],
            "num_medication_pairs_checked": len(medications) * (len(medications) - 1) // 2
        }

    def _get_recommendation(self, severity: str) -> str:
        """Get recommendation based on severity."""
        recommendations = {
            "Mild": "Monitor patient for mild side effects",
            "Moderate": "Consider dose adjustment or monitoring. Consult pharmacist",
            "Severe": "Avoid combination or monitor INR/therapeutic levels closely"
        }
        return recommendations.get(severity, "Consult drug reference")

    def _generate_alternatives(self, medications: List[str], interactions: List[Dict]) -> List[Dict]:
        """Generate alternative medication suggestions."""
        alternatives = []

        if not interactions:
            return alternatives

        # Get drugs involved in problematic interactions
        problematic_drugs = set()
        for interaction in interactions:
            problematic_drugs.update(interaction["drug_pair"])

        # For each problematic drug, suggest alternatives
        alternative_suggestions = {
            "Aspirin": ["Clopidogrel", "Ticagrelor"],
            "Warfarin": ["Apixaban", "Rivaroxaban"],
            "NSAIDs": ["Acetaminophen", "COX-2 inhibitors"],
            "ACE Inhibitors": ["ARBs", "Beta-blockers"],
        }

        for drug in list(problematic_drugs)[:2]:
            if drug in alternative_suggestions:
                for alt_drug in alternative_suggestions[drug][:1]:
                    alternatives.append({
                        "replace": drug,
                        "with": alt_drug,
                        "reason": f"Lower interaction risk with other medications"
                    })

        return alternatives

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate interaction classifier.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary with evaluation metrics
        """
        if self.interaction_classifier is None:
            return {"error": "Classifier not trained"}

        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        y_pred = self.interaction_classifier.predict(X_test)
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
            path = str(DRUG_INTERACTION_MODEL)

        model_data = {
            "tfidf_vectorizer": self.tfidf_vectorizer,
            "interaction_classifier": self.interaction_classifier,
            "interaction_database": self.interaction_database,
            "drug_names": self.drug_names,
        }
        joblib.dump(model_data, path)
        print(f"Drug interaction scorer saved to {path}")

    def load_model(self, path: str = None) -> None:
        """Load model from disk."""
        if path is None:
            path = str(DRUG_INTERACTION_MODEL)

        model_data = joblib.load(path)
        self.tfidf_vectorizer = model_data["tfidf_vectorizer"]
        self.interaction_classifier = model_data["interaction_classifier"]
        self.interaction_database = model_data["interaction_database"]
        self.drug_names = model_data["drug_names"]
        self.is_trained = True
        print(f"Drug interaction scorer loaded from {path}")


if __name__ == "__main__":
    """Demo: Test drug interaction scorer"""
    from utils.synthetic_data import generate_drug_pairs

    print("Generating synthetic drug pair data...")
    drugs_df = generate_drug_pairs(200)

    scorer = DrugInteractionScorer()
    scorer.train(drugs_df)

    test_cases = [
        {"medications": ["Metformin", "Aspirin", "Lisinopril"]},
        {"medications": ["Warfarin", "Aspirin"]},
        {"medications": ["Amoxicillin", "Ibuprofen", "Omeprazole"]},
    ]

    print("\nTesting drug interactions:")
    for i, test_input in enumerate(test_cases, 1):
        result = scorer.predict(test_input)
        print(f"\nTest Case {i}: {test_input['medications']}")
        print(f"  Risk Score: {result['total_risk_score']}")
        print(f"  Safe to Prescribe: {result['safe_to_prescribe']}")
        if result['interactions_found']:
            print(f"  Interactions Found:")
            for interaction in result['interactions_found']:
                print(f"    - {interaction['drug_pair']}: {interaction['severity']}")

    print("\nSaving model...")
    scorer.save_model()
