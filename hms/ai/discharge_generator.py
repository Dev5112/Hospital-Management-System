"""
Discharge Summary Generator using Claude API.
Creates comprehensive discharge documents for patients.
"""

import sys
import json
from typing import Dict, List, Any
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, DISCHARGE_GENERATOR_CONFIG
from anthropic import Anthropic


class DischargeGenerator:
    """
    Automated discharge summary and letter generator using Claude.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize discharge generator.

        Args:
            api_key: Anthropic API key
        """
        if api_key is None:
            api_key = ANTHROPIC_API_KEY

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL

    def build_prompt(self, admission_data: dict) -> str:
        """
        Build prompt for generating discharge summary.

        Args:
            admission_data: Dictionary with admission and treatment details

        Returns:
            Formatted prompt
        """
        prompt = f"""You are an experienced hospital discharge coordinator. Generate a comprehensive discharge summary based on the following patient information:

ADMISSION DETAILS:
- Patient: {admission_data.get('patient_name', 'Patient')}
- Age: {admission_data.get('age', 'Unknown')}
- Admission Date: {admission_data.get('admission_date', 'Unknown')}
- Discharge Date: {admission_data.get('discharge_date', 'Unknown')}
- Ward: {admission_data.get('ward', 'Unknown')}
- Primary Diagnosis: {admission_data.get('diagnosis', 'Unknown')}

CLINICAL COURSE:
{', '.join(admission_data.get('treatment_notes', []))}

MEDICATIONS PRESCRIBED:
{json.dumps(admission_data.get('medications_prescribed', []), indent=2)}

LAB RESULTS:
{json.dumps(admission_data.get('lab_results', {}), indent=2)}

FOLLOW-UP REQUIRED: {admission_data.get('follow_up_required', False)}

Generate ONLY valid JSON with this exact structure:
{{
  "patient_letter": "<Warm, professional letter to patient explaining their stay and what to do>",
  "clinical_summary": "<Concise clinical summary for medical records>",
  "medication_schedule": [
    {{
      "drug": "<drug name>",
      "dose": "<dose>",
      "frequency": "<how often>",
      "duration": "<how long to take>",
      "instructions": "<special instructions>"
    }}
  ],
  "follow_up_instructions": "<When and where to follow up, what to watch for>",
  "warning_signs": "<Symptoms requiring immediate return to hospital>",
  "diet_advice": "<Dietary recommendations>",
  "activity_restrictions": "<Any activity limitations>",
  "wound_care": "<If applicable, wound care instructions>"
}}

Ensure all text is clear, compassionate, and avoids jargon where possible."""

        return prompt

    def generate(self, admission_data: dict) -> dict:
        """
        Generate discharge summary.

        Args:
            admission_data: Dictionary with admission details

        Returns:
            Dictionary with generated discharge documents
        """
        prompt = self.build_prompt(admission_data)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=DISCHARGE_GENERATOR_CONFIG["max_tokens"],
            messages=[{"role": "user", "content": prompt}],
            temperature=DISCHARGE_GENERATOR_CONFIG["temperature"]
        )

        import json
        try:
            response_text = response.content[0].text
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])
            else:
                result = self._template()
        except Exception as e:
            print(f"Error parsing response: {e}")
            result = self._template()

        return result

    def _template(self) -> dict:
        """Provide default template."""
        return {
            "patient_letter": "Dear Patient, Thank you for choosing our hospital for your care.",
            "clinical_summary": "Patient admitted and discharged without complications.",
            "medication_schedule": [],
            "follow_up_instructions": "Follow up with your primary care physician.",
            "warning_signs": "Return immediately if experiencing chest pain or difficulty breathing.",
            "diet_advice": "Resume normal diet as tolerated.",
            "activity_restrictions": "Avoid strenuous activity for 1-2 weeks.",
            "wound_care": "Not applicable."
        }

    def run(self, admission_data: dict) -> dict:
        """
        Run discharge generator.

        Args:
            admission_data: Admission details dictionary

        Returns:
            Complete discharge package
        """
        print("Generating discharge summary...")
        summary = self.generate(admission_data)

        print("\n" + "="*70)
        print("PATIENT DISCHARGE LETTER")
        print("="*70)
        print(f"\n{summary.get('patient_letter', '')}\n")

        print("="*70)
        print("MEDICATION SCHEDULE")
        print("="*70)
        medications = summary.get('medication_schedule', [])
        if medications:
            for med in medications:
                print(f"\n{med.get('drug', 'Unknown')}:")
                print(f"  Dose: {med.get('dose', 'N/A')}")
                print(f"  Frequency: {med.get('frequency', 'N/A')}")
                print(f"  Duration: {med.get('duration', 'N/A')}")
                print(f"  Instructions: {med.get('instructions', 'N/A')}")
        else:
            print("No medications prescribed.")

        print("\n" + "="*70)
        print("FOLLOW-UP CARE")
        print("="*70)
        print(f"\n{summary.get('follow_up_instructions', '')}\n")

        print("⚠️  WARNING SIGNS - Return to Hospital If:")
        print(f"{summary.get('warning_signs', '')}\n")

        print("="*70)
        print("CLINICAL SUMMARY (For Medical Records)")
        print("="*70)
        print(f"\n{summary.get('clinical_summary', '')}\n")

        print("="*70)
        print("LIFESTYLE RECOMMENDATIONS")
        print("="*70)
        print(f"\nDiet: {summary.get('diet_advice', 'N/A')}")
        print(f"Activity: {summary.get('activity_restrictions', 'N/A')}")
        if summary.get('wound_care') and summary.get('wound_care').lower() != 'not applicable':
            print(f"Wound Care: {summary.get('wound_care', 'N/A')}")

        return summary


if __name__ == "__main__":
    """Demo: Test discharge generator"""
    sample_admission = {
        "patient_name": "John D.",
        "age": 67,
        "admission_date": "2025-11-20",
        "discharge_date": "2025-11-27",
        "ward": "Cardiology",
        "diagnosis": "Acute Myocardial Infarction (AMI) - Anterior Wall",
        "treatment_notes": [
            "Admitted with chest pain and elevated troponin",
            "Underwent coronary angiography with stent placement to LAD",
            "Post-procedure angiography showed good stent patency",
            "Serial troponin peaked at 4.2 ng/mL",
            "Echocardiogram showed mild anterior wall hypokinesis",
            "Tolerated diet well, ambulating independently"
        ],
        "medications_prescribed": [
            {
                "drug": "Ticagrelor",
                "dose": "60mg",
                "frequency": "Twice daily",
                "duration": "12 months",
                "instructions": "Do not skip doses. Take with food if possible."
            },
            {
                "drug": "Aspirin",
                "dose": "81mg",
                "frequency": "Once daily",
                "duration": "Indefinitely",
                "instructions": "Take every morning"
            },
            {
                "drug": "Lisinopril",
                "dose": "5mg",
                "frequency": "Once daily",
                "duration": "Ongoing",
                "instructions": "Monitor blood pressure. May cause dizziness initially."
            },
            {
                "drug": "Atorvastatin",
                "dose": "80mg",
                "frequency": "Once daily at bedtime",
                "duration": "Ongoing",
                "instructions": "High intensity statin therapy"
            },
            {
                "drug": "Metoprolol",
                "dose": "50mg",
                "frequency": "Twice daily",
                "duration": "Ongoing",
                "instructions": "Monitor heart rate and blood pressure"
            }
        ],
        "lab_results": {
            "Troponin Peak": "4.2 ng/mL",
            "CK-MB": "320 U/L",
            "Hemoglobin": "14.2 g/dL",
            "Creatinine": "0.95 mg/dL"
        },
        "follow_up_required": True
    }

    generator = DischargeGenerator()
    summary = generator.run(sample_admission)
