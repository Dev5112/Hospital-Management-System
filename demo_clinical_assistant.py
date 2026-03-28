"""
Demo: Clinical Decision Support Assistant for HMS

This demo shows how to use the ClinicalDecisionSupport module.

IMPORTANT: This module requires a valid Anthropic API key from
https://console.anthropic.com (NOT the VSCode LM key).

To use this demo in your own environment:
1. Sign up for Anthropic API at https://console.anthropic.com
2. Create an API key
3. Set environment variable: export ANTHROPIC_API_KEY=sk_...
4. Run this script

In Claude Code environment: VSCode LM key returns raw events instead of
parsed Messages, so real API calls won't work. Use your own environment.
"""

import json
import sys
from clinical_decision_support import ClinicalDecisionSupport
from database import DatabaseManager


def show_example_output():
    """Show what a real clinical decision support looks like."""
    print("=" * 80)
    print("Example Clinical Decision Support Output")
    print("=" * 80)

    example_suggestion = {
        "analyzed_at": "2026-03-28T10:30:00",
        "patient_id": 1,
        "proposed_diagnosis": "Type 2 Diabetes Mellitus",
        "proposed_prescription": "Metformin 500mg twice daily",
        "diagnosis_assessment": "Consistent with patient's age (52), family history, and elevated glucose. Appropriate for initial management.",
        "contraindications": [],
        "clinical_concerns": [
            "Check kidney function (eGFR) before starting Metformin",
            "Assess for metformin contraindications (hepatic/renal impairment)"
        ],
        "guideline_references": "ADA 2024 Guidelines recommend Metformin as first-line therapy for type 2 diabetes. Check HbA1c baseline before treatment.",
        "risk_level": "low",
        "recommendations": [
            "Baseline HbA1c and fasting glucose measurement",
            "Kidney function assessment (eGFR, creatinine)",
            "Patient education on diet and exercise",
            "Follow-up in 3 months to assess glycemic control"
        ],
        "confidence": 0.92
    }

    print(f"\nRisk Level: {example_suggestion['risk_level'].upper()}")
    print(f"\nDiagnosis Assessment:\n{example_suggestion['diagnosis_assessment']}")
    print(f"\nClinical Concerns:")
    for concern in example_suggestion['clinical_concerns']:
        print(f"  ⚠️  {concern}")
    print(f"\nGuideline References:\n{example_suggestion['guideline_references']}")
    print(f"\nRecommendations:")
    for rec in example_suggestion['recommendations']:
        print(f"  ✓ {rec}")
    print(f"\nConfidence: {example_suggestion['confidence']:.1%}")


def demo_with_real_api():
    """Demo clinical decision support with real API call."""
    print("\n" + "=" * 80)
    print("Clinical Decision Support - Real API Test")
    print("=" * 80)

    try:
        # Initialize
        cds = ClinicalDecisionSupport()
        db = DatabaseManager("hms_database.db")

        # List available patients
        print("\nAvailable patients:")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT patient_id, name FROM patients LIMIT 5")
            for pid, name in cursor.fetchall():
                print(f"  - Patient {pid}: {name}")

        # Test with first patient
        print("\n" + "-" * 80)
        print("Testing Diagnosis: Type 2 Diabetes Mellitus")
        print("Testing Prescription: Metformin 500mg twice daily")
        print("-" * 80)

        suggestion = cds.analyze_diagnosis(
            patient_id=1,
            proposed_diagnosis="Type 2 Diabetes Mellitus",
            proposed_prescription="Metformin 500mg twice daily",
            db_manager=db
        )

        print("\n✓ Clinical Suggestion:")
        print(cds.get_suggestion_summary(suggestion))

        # Save result to file for inspection
        with open("clinical_suggestion_result.json", "w") as f:
            json.dump(suggestion, f, indent=2)
        print(f"\n✓ Result saved to clinical_suggestion_result.json")

    except ValueError as e:
        if "VSCode LM key" in str(e) or "vscode-lm" in str(e):
            print(f"\n⚠️  Cannot run in Claude Code environment (VSCode LM API issue)")
            print(f"\nTo run this demo, you need:")
            print(f"1. A proper Anthropic API key from https://console.anthropic.com")
            print(f"2. Your own Python environment (not Claude Code)")
            print(f"3. Set: export ANTHROPIC_API_KEY=sk_...")
            print(f"4. Then run: python3 demo_clinical_assistant.py")
            show_example_output()
        else:
            print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def list_available_patients():
    """List all available patients in HMS for testing."""
    print("\n" + "=" * 80)
    print("Available Patients in HMS Database")
    print("=" * 80)

    db = DatabaseManager("hms_database.db")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT patient_id, name, blood_group,
                   (SELECT COUNT(*) FROM medical_records WHERE patient_id = patients.patient_id) as visits
            FROM patients
            ORDER BY patient_id
        """)

        patients = cursor.fetchall()

        if not patients:
            print("No patients found. Please seed database first.")
            return

        print(f"\n{'ID':<5} {'Name':<30} {'Blood Type':<12} {'Visits':<6}")
        print("-" * 60)

        for patient in patients:
            print(f"{patient[0]:<5} {patient[1]:<30} {patient[2]:<12} {patient[3]:<6}")


def show_module_usage():
    """Show how to use the ClinicalDecisionSupport module."""
    print("\n" + "=" * 80)
    print("Module Usage Guide")
    print("=" * 80)

    usage_code = '''
# Import the module
from clinical_decision_support import ClinicalDecisionSupport
from database import DatabaseManager

# Initialize with your API key
cds = ClinicalDecisionSupport(anthropic_api_key="sk_...")

# Get database instance
db = DatabaseManager("hms_database.db")

# Analyze a diagnosis
suggestion = cds.analyze_diagnosis(
    patient_id=1,
    proposed_diagnosis="Type 2 Diabetes Mellitus",
    proposed_prescription="Metformin 500mg twice daily",
    db_manager=db
)

# Display suggestion
print(cds.get_suggestion_summary(suggestion))

# Access raw data
print(f"Risk Level: {suggestion['risk_level']}")
print(f"Contraindications: {suggestion['contraindications']}")
print(f"Confidence: {suggestion['confidence']:.1%}")
    '''

    print(usage_code)

    print("\nRequired Environment Setup:")
    print("=" * 80)
    print("""
1. Get Anthropic API Key:
   - Visit https://console.anthropic.com
   - Sign up / login
   - Create API key
   - Keep it secret!

2. Set environment variable:
   export ANTHROPIC_API_KEY=sk_...

3. Install requirements:
   pip install anthropic

4. Run in your own Python environment (NOT in Claude Code):
   python3 demo_clinical_assistant.py
    """)


if __name__ == "__main__":
    # Show available patients
    list_available_patients()

    # Show usage guide
    show_module_usage()

    # Try to run with real API
    print("\nAttempting to connect to Claude API...")
    demo_with_real_api()

    print("\n" + "=" * 80)
    print("Clinical Decision Support Demo - Complete")
    print("=" * 80)
    print("\nNext steps for deployment:")
    print("1. Get your Anthropic API key from https://console.anthropic.com")
    print("2. Create Flask endpoints to wrap this module (Phase 2)")
    print("3. Add database logging of suggestions and doctor decisions")
    print("4. Build UI sidebar to display suggestions to doctors")
    print("5. Track acceptance rates and metrics")
