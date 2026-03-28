"""
Predictive Alert Narrator using Claude API.
Converts ML predictions into clinical narratives for alerts.
"""

import sys
import json
from typing import Dict, List, Any
from datetime import datetime
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, ALERT_NARRATOR_CONFIG
from anthropic import Anthropic


class AlertNarrator:
    """
    Converts raw ML predictions into clinical alert narratives.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize alert narrator.

        Args:
            api_key: Anthropic API key
        """
        if api_key is None:
            api_key = ANTHROPIC_API_KEY

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL

    def build_prompt(self, alert_context: dict) -> str:
        """
        Build prompt for alert narration.

        Args:
            alert_context: Dictionary with alert type and ML output

        Returns:
            Formatted prompt
        """
        alert_type = alert_context.get("alert_type", "unknown")
        ml_output = alert_context.get("ml_output", {})
        patient_context = alert_context.get("patient_context", {})
        audience = alert_context.get("audience", "nurse")

        audience_guidance = {
            "nurse": "Address practical nursing actions and patient monitoring. Use clinical language but avoid overly technical jargon.",
            "doctor": "Focus on clinical significance and diagnostic/treatment implications. Be concise and direct.",
            "admin": "Emphasize operational and resource implications. Explain why this alert matters for hospital operations."
        }

        guidance = audience_guidance.get(audience, "")

        prompt = f"""You are a clinical alert coordinator generating narratives for hospital alerts. Convert the following raw prediction data into a professional, actionable clinical alert narrative.

ALERT TYPE: {alert_type}

ML PREDICTION OUTPUT:
{json.dumps(ml_output, indent=2)}

PATIENT CONTEXT (if available):
{json.dumps(patient_context, indent=2)}

TARGET AUDIENCE: {audience.upper()}
{guidance}

Generate ONLY valid JSON with this exact structure:
{{
  "alert_title": "<Bold, attention-grabbing title with emoji appropriate to severity>",
  "narrative": "<2-3 paragraph clinical narrative explaining the alert in plain English. Start with who/what/when, then explain clinical significance, then actionable next steps>",
  "priority": "Low|Medium|High|Critical",
  "action_items": [
    "<Specific, actionable item 1>",
    "<Specific, actionable item 2>"
  ],
  "generated_at": "{datetime.now().isoformat()}"
}}

Requirements:
- Narrative should be 150-300 words
- Use clinical terminology appropriately for the audience
- Be urgent but not alarming
- Focus on actionable items
- Include specific patient identifiers or location if available
- Provide clear next steps"""

        return prompt

    def narrate(self, alert_context: dict) -> dict:
        """
        Generate alert narrative.

        Args:
            alert_context: Dictionary with alert details

        Returns:
            Structured alert narrative
        """
        prompt = self.build_prompt(alert_context)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=ALERT_NARRATOR_CONFIG["max_tokens"],
            messages=[{"role": "user", "content": prompt}],
            temperature=ALERT_NARRATOR_CONFIG["temperature"]
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
            "alert_title": "⚠️ Clinical Alert",
            "narrative": "A clinical alert has been generated requiring medical review.",
            "priority": "Medium",
            "action_items": [
                "Review alert details",
                "Consult with appropriate clinical team",
                "Take necessary action"
            ],
            "generated_at": datetime.now().isoformat()
        }

    def run(self, alert_context: Dict[str, Any]) -> dict:
        """
        Run alert narrator.

        Args:
            alert_context: Dictionary with:
                - alert_type: str (readmission/bed_overflow/fraud/no_show/drug)
                - ml_output: dict (raw prediction)
                - patient_context: dict (optional)
                - audience: str (nurse/doctor/admin)

        Returns:
            Complete alert narrative
        """
        alert = self.narrate(alert_context)

        # Visual formatting based on priority
        priority_colors = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢"
        }

        priority = alert.get("priority", "Medium")
        emoji = priority_colors.get(priority, "⚠️")

        print(f"\n{emoji} " + "="*70)
        print(f"{alert.get('alert_title', 'Alert')}")
        print("="*70)

        print(f"\n{alert.get('narrative', '')}\n")

        print("ACTION ITEMS:")
        for i, action in enumerate(alert.get('action_items', []), 1):
            print(f"  {i}. {action}")

        print(f"\nPriority: {priority}")
        print(f"Generated: {alert.get('generated_at', 'Unknown')}")
        print("="*70 + "\n")

        return alert


if __name__ == "__main__":
    """Demo: Test alert narrator with different alert types"""
    narr = AlertNarrator()

    # Demo 1: High Readmission Risk Alert
    alert_context_1 = {
        "alert_type": "readmission",
        "ml_output": {
            "risk_score": 78,
            "risk_category": "High",
            "readmission_probability": 0.78,
            "top_risk_factors": [
                "3 previous admissions in 6 months",
                "Low medication adherence (0.4)",
                "Multiple comorbidities (Diabetes, Hypertension)"
            ],
            "recommendation": "Schedule follow-up within 7 days"
        },
        "patient_context": {
            "patient_id": "P12345",
            "name": "John D.",
            "age": 67,
            "ward": "Ward B, Bed 12",
            "diagnosis": "Type 2 Diabetes with complications",
            "admission_date": "2025-11-20"
        },
        "audience": "nurse"
    }

    print("Demo 1: Readmission Risk Alert (Nurse Audience)")
    narr.run(alert_context_1)

    # Demo 2: Bed Overflow Alert
    alert_context_2 = {
        "alert_type": "bed_overflow",
        "ml_output": {
            "ward": "ICU",
            "peak_day": "2025-12-05",
            "overflow_risk": True,
            "peak_occupancy": 24,
            "ward_capacity": 25,
            "recommended_action": "Pre-arrange 4 additional ICU beds by Dec 4"
        },
        "patient_context": {},
        "audience": "admin"
    }

    print("\nDemo 2: Bed Overflow Alert (Admin Audience)")
    narr.run(alert_context_2)

    # Demo 3: Fraud Detection Alert
    alert_context_3 = {
        "alert_type": "fraud",
        "ml_output": {
            "anomaly_score": 0.91,
            "is_fraud": True,
            "fraud_type": "Upcoding",
            "suspicious_services": ["MRI x3", "ICU charge on outpatient"],
            "explanation": "Bill is 3.2x above average for this diagnosis"
        },
        "patient_context": {
            "bill_id": "B98765",
            "patient_name": "Jane S.",
            "department": "Neurology",
            "bill_amount": "$24,500"
        },
        "audience": "doctor"
    }

    print("\nDemo 3: Fraud Detection Alert (Doctor Audience)")
    narr.run(alert_context_3)
