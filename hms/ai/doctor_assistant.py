"""
Doctor's Patient Assistant using Claude API.
Provides patient context-aware information from medical records.
"""

import sys
import json
from typing import Dict, Any
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from anthropic import Anthropic


class DoctorAssistant:
    """
    Context-aware doctor assistant powered by Claude.
    Uses RAG pattern to answer questions from patient records.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize doctor assistant.

        Args:
            api_key: Anthropic API key
        """
        if api_key is None:
            api_key = ANTHROPIC_API_KEY

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL

    def build_system_prompt(self, patient_context: dict) -> str:
        """
        Build system prompt with patient context.

        Args:
            patient_context: Patient's medical record

        Returns:
            System prompt with context
        """
        context_str = json.dumps(patient_context, indent=2, default=str)

        return f"""You are a knowledgeable clinical assistant helping a physician manage patient care.

You have access to the patient's current medical record:

{context_str}

Instructions:
1. Answer questions ONLY from the provided patient context
2. Be direct and clinically accurate
3. If information is not in the record, clearly state: "This information is not available in the patient's records."
4. Provide specific values, dates, and details when asking
5. Flag any potential concerns (e.g., drug interactions, abnormal values)
6. Do not make assumptions or speculate
7. Always cite the source of information (e.g., "Last visit on 2025-11-27")

Your responses should help the doctor make informed clinical decisions."""

    def call_claude(self, doctor_query: str, patient_context: dict) -> str:
        """
        Call Claude with patient context.

        Args:
            doctor_query: Doctor's natural language question
            patient_context: Patient medical record

        Returns:
            Claude's response
        """
        system_prompt = self.build_system_prompt(patient_context)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=system_prompt,
            messages=[
                {"role": "user", "content": doctor_query}
            ],
            temperature=0.3
        )

        return response.content[0].text

    def extract_sources(self, patient_context: dict, query: str) -> list:
        """
        Extract relevant sources from patient context based on query.

        Args:
            patient_context: Patient record
            query: Doctor's query

        Returns:
            List of relevant source identifiers
        """
        sources = []

        query_lower = query.lower()

        # Check for key term matches
        if any(term in query_lower for term in ["medication", "drug", "prescription"]):
            if "medications" in patient_context:
                sources.append("medication_list")
            if "prescriptions" in patient_context:
                sources.append("prescriptions")

        if any(term in query_lower for term in ["visit", "appointment", "consultation", "last"]):
            if "recent_visits" in patient_context:
                sources.append("recent_visits")
            if "admission_record" in patient_context:
                sources.append("admission_record")

        if any(term in query_lower for term in ["lab", "result", "test", "glucose", "hemoglobin"]):
            if "lab_results" in patient_context:
                sources.append("lab_results")

        if any(term in query_lower for term in ["diagnosis", "condition", "disease"]):
            if "diagnoses" in patient_context:
                sources.append("diagnoses")

        if any(term in query_lower for term in ["allerg", "intolerance"]):
            if "allergies" in patient_context:
                sources.append("allergies")

        if not sources:
            sources = list(patient_context.keys())[:3]

        return sources

    def run(self, patient_context: dict, doctor_query: str = None) -> dict:
        """
        Run doctor assistant.

        Args:
            patient_context: Patient medical record dictionary
            doctor_query: Optional query (if None, user input from stdin)

        Returns:
            Dictionary with answer and metadata
        """
        if doctor_query is None:
            print("=== Doctor's Patient Assistant ===")
            print("\nPatient Context Loaded:")
            print(f"  Patient ID: {patient_context.get('patient_id', 'Unknown')}")
            print(f"  Age: {patient_context.get('age', 'Unknown')}")
            print(f"  Diagnoses: {', '.join(patient_context.get('diagnoses', []))}")

            print("\nEnter your query (type 'exit' to quit):")
            doctor_query = input("Doctor: ").strip()

            if doctor_query.lower() in ["exit", "quit"]:
                return {}

        # Get relevant sources
        sources = self.extract_sources(patient_context, doctor_query)

        # Call Claude
        answer = self.call_claude(doctor_query, patient_context)

        # Confidence assessment
        if "not available" in answer.lower() or "not in" in answer.lower():
            confidence = "medium"
        elif "based on" in answer.lower() or "from" in answer.lower():
            confidence = "high"
        else:
            confidence = "medium"

        result = {
            "query": doctor_query,
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "caveats": "Information based on current medical records. Always verify critical decisions."
        }

        print("\n" + "="*60)
        print("Doctor Assistant Response")
        print("="*60)
        print(f"\nAnswer:\n{answer}")
        print(f"\nSources Used: {', '.join(sources)}")
        print(f"Confidence: {confidence.title()}")
        print(f"\n⚠️  Caveats: {result['caveats']}")

        return result

    def batch_queries(self, patient_context: dict, queries: list) -> list:
        """
        Process multiple queries for same patient.

        Args:
            patient_context: Patient medical record
            queries: List of doctor queries

        Returns:
            List of result dictionaries
        """
        results = []
        for query in queries:
            result = self.run(patient_context, query)
            results.append(result)
        return results


if __name__ == "__main__":
    """Demo: Test doctor assistant"""
    sample_patient = {
        "patient_id": "P12345",
        "name": "John D.",
        "age": 67,
        "gender": "M",
        "diagnoses": ["Type 2 Diabetes", "Hypertension", "Dyslipidemia"],
        "medications": [
            {"drug": "Metformin", "dose": "500mg", "frequency": "Twice daily"},
            {"drug": "Lisinopril", "dose": "10mg", "frequency": "Once daily"},
            {"drug": "Atorvastatin", "dose": "20mg", "frequency": "Once daily"},
            {"drug": "Aspirin", "dose": "81mg", "frequency": "Once daily"},
        ],
        "allergies": ["Penicillin", "Sulfonamides"],
        "lab_results": {
            "HbA1c": "8.2%",
            "Fasting glucose": "156 mg/dL",
            "Total cholesterol": "245 mg/dL",
            "Creatinine": "1.15 mg/dL",
            "GFR": "68 mL/min"
        },
        "recent_visits": [
            {"date": "2025-11-27", "summary": "Routine follow-up, diabetes control suboptimal"},
            {"date": "2025-10-15", "summary": "Blood pressure management reviewed"}
        ],
        "last_admission": "None",
    }

    assistant = DoctorAssistant()

    # Demo queries
    demo_queries = [
        "What medications is this patient on?",
        "Are there any drug interactions I should worry about?",
        "What was the last HbA1c and is control adequate?",
        "Does this patient have any medication allergies?",
    ]

    print("Processing sample queries:\n")
    for query in demo_queries:
        print(f"\nQuery: {query}")
        result = assistant.run(sample_patient, query)
        print()
