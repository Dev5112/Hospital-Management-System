"""
Medical Report Summarizer using Claude API.
Converts clinical reports to patient-friendly or clinical summaries.
"""

import sys
from typing import Dict, List, Any
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, REPORT_SUMMARIZER_CONFIG
from anthropic import Anthropic


class ReportSummarizer:
    """
    Medical report summarizer with audience-specific outputs.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize summarizer.

        Args:
            api_key: Anthropic API key
        """
        if api_key is None:
            api_key = ANTHROPIC_API_KEY

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL

    def build_patient_prompt(self, report_text: str) -> str:
        """Build prompt for patient-friendly summary."""
        return f"""You are a medical writer translating clinical reports for patients. Your goal is to:

1. Use simple, non-technical language
2. Explain what the tests mean in plain English
3. Highlight any abnormal findings
4. Provide context about next steps

Clinical Report:
{report_text}

Provide a JSON response with this exact structure:
{{
  "plain_summary": "<2-3 sentences explaining the key findings in simple terms>",
  "abnormal_values": [
    {{
      "test": "<test name>",
      "value": "<the patient's value>",
      "normal": "<what's considered normal>",
      "meaning": "<plain English explanation>"
    }}
  ],
  "next_steps": "<what the patient should do now>",
  "disclaimer": "This is AI-generated. Always consult with your doctor about results."
}}"""

    def build_doctor_prompt(self, report_text: str) -> str:
        """Build prompt for clinical summary."""
        return f"""You are a clinical summarizer creating concise summaries for physicians. Provide:

1. Clinical interpretation of results
2. Abnormal findings flagged for attention
3. Differential diagnoses to consider
4. Recommended follow-up

Clinical Report:
{report_text}

Provide a JSON response with this exact structure:
{{
  "clinical_summary": "<concise clinical interpretation>",
  "flagged_values": [
    {{
      "test": "<test name>",
      "value": "<value>",
      "clinical_significance": "<why this matters>"
    }}
  ],
  "differential_considerations": ["<diagnosis 1>", "<diagnosis 2>"],
  "suggested_follow_up": "<recommended investigations or referrals>"
}}"""

    def summarize(self, report_text: str, audience: str = "patient") -> dict:
        """
        Summarize medical report.

        Args:
            report_text: Raw medical report text
            audience: "patient" or "doctor"

        Returns:
            Dictionary with summarized report
        """
        if audience == "patient":
            prompt = self.build_patient_prompt(report_text)
        else:
            prompt = self.build_doctor_prompt(report_text)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=REPORT_SUMMARIZER_CONFIG["temperature"]
        )

        import json
        try:
            response_text = response.content[0].text
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])
            else:
                result = self._default_summary(audience)
        except Exception as e:
            print(f"Error parsing response: {e}")
            result = self._default_summary(audience)

        return {
            "audience": audience,
            "summary": result,
            "source_length": len(report_text)
        }

    def _default_summary(self, audience: str) -> dict:
        """Provide default summary."""
        if audience == "patient":
            return {
                "plain_summary": "Your lab results show some values that need to be reviewed by your doctor.",
                "abnormal_values": [],
                "next_steps": "Schedule a follow-up appointment with your healthcare provider.",
                "disclaimer": "This is AI-generated. Always consult with your doctor about results."
            }
        else:
            return {
                "clinical_summary": "Lab work shows findings requiring clinical correlation.",
                "flagged_values": [],
                "differential_considerations": [],
                "suggested_follow_up": "Clinical assessment recommended."
            }

    def run(self, report_text: str, audience: str = "patient") -> dict:
        """
        Run summarizer.

        Args:
            report_text: Medical report text
            audience: "patient" or "doctor"

        Returns:
            Summary dictionary
        """
        result = self.summarize(report_text, audience)

        print("\n" + "="*60)
        print(f"Medical Report Summary ({audience.title()} Version)")
        print("="*60)

        summary_data = result["summary"]

        if audience == "patient":
            print(f"\n{summary_data.get('plain_summary', '')}\n")

            if summary_data.get("abnormal_values"):
                print("Notable Results:")
                for value in summary_data.get("abnormal_values", []):
                    print(f"  • {value.get('test', 'Unknown')}: {value.get('meaning', 'N/A')}")

            print(f"\nNext Steps: {summary_data.get('next_steps', 'See your doctor')}")
            print(f"\n⚠️  {summary_data.get('disclaimer', '')}")
        else:
            print(f"\n{summary_data.get('clinical_summary', '')}\n")

            if summary_data.get("flagged_values"):
                print("Flagged Results:")
                for value in summary_data.get("flagged_values", []):
                    print(f"  • {value.get('test', '')}: {value.get('clinical_significance', '')}")

            if summary_data.get("differential_considerations"):
                print(f"\nDifferential Diagnoses:")
                for dx in summary_data.get("differential_considerations", []):
                    print(f"  • {dx}")

            print(f"\nRecommended Follow-up: {summary_data.get('suggested_follow_up', '')}")

        return result


if __name__ == "__main__":
    """Demo: Test report summarizer"""
    sample_report = """
    Date: 2025-11-28
    Patient: John D.
    Age: 67

    LABORATORY RESULTS:
    - HbA1c: 8.2% (Normal: <5.7%) - ELEVATED
    - Fasting Glucose: 156 mg/dL (Normal: 70-100) - ELEVATED
    - Total Cholesterol: 245 mg/dL (Normal: <200) - ELEVATED
    - LDL: 165 mg/dL (Normal: <100) - HIGH
    - HDL: 38 mg/dL (Normal: >40) - LOW
    - Triglycerides: 285 mg/dL (Normal: <150) - ELEVATED
    - Creatinine: 1.2 mg/dL (Normal: 0.6-1.2) - HIGH-NORMAL
    - GFR: 68 mL/min (Normal: >60) - MILDLY REDUCED

    IMPRESSION:
    Poorly controlled Type 2 Diabetes with dyslipidemia and early renal dysfunction.
    """

    summarizer = ReportSummarizer()

    print("Patient Summary:")
    summarizer.run(sample_report, audience="patient")

    print("\n\nPhysician Summary:")
    summarizer.run(sample_report, audience="doctor")
