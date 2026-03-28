"""
Clinical Decision Support Assistant for Hospital Management System

Provides real-time clinical validation using Claude API before doctors confirm diagnoses.
Checks diagnosis consistency with patient data, drug interactions, and clinical guidelines.

All suggestions are advisory (non-overriding) and logged for audit trail tracking.

NOTE: This module requires a valid Anthropic API key (from https://console.anthropic.com).
The key should be set in the ANTHROPIC_API_KEY environment variable.

For production use, see: https://docs.anthropic.com/en/api/getting-started
"""

import json
import re
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("Warning: anthropic SDK not installed. Install with: pip install anthropic")
    anthropic = None


class ClinicalDecisionSupport:
    """
    Clinical decision support using Claude Opus 4.6 with adaptive thinking.

    Validates proposed diagnoses and prescriptions against:
    - Patient demographics, vitals, and medical history
    - Drug interactions and contraindications
    - Current clinical guidelines

    Returns structured suggestions with risk assessment (advisory only).
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize Clinical Decision Support.

        Args:
            anthropic_api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
                              IMPORTANT: Use a real API key from https://console.anthropic.com
                              NOT the VSCode LM key (which returns streaming events).
        """
        if anthropic is None:
            raise ImportError("anthropic SDK required. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self._validate_api_key()

    def _validate_api_key(self):
        """Validate that we have a proper Anthropic API key, not a VSCode LM key."""
        import os
        key = os.getenv('ANTHROPIC_API_KEY', '')
        if key.startswith('vscode-lm-'):
            raise ValueError(
                "ERROR: Using VSCode LM key instead of Anthropic API key.\n"
                "Please get a real API key from https://console.anthropic.com\n"
                "VSCode LM keys return raw streaming events, not parsed Messages."
            )

    def analyze_diagnosis(
        self,
        patient_id: int,
        proposed_diagnosis: str,
        proposed_prescription: str,
        db_manager: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze proposed diagnosis and prescription against patient profile.

        Args:
            patient_id: Patient ID from HMS database
            proposed_diagnosis: Proposed diagnosis text (e.g., "Type 2 Diabetes")
            proposed_prescription: Proposed prescription (e.g., "Metformin 500mg daily")
            db_manager: DatabaseManager instance to fetch patient data.
                       If None, uses minimal patient context.

        Returns:
            Structured suggestion dict with:
            - diagnosis_assessment: Consistency check
            - contraindications: List of drug interactions/allergies
            -clinical_concerns: List of clinical red flags
            - guideline_references: Relevant clinical guidelines
            - risk_level: low|moderate|high|critical
            - recommendations: Suggested actions
            - confidence: 0.0-1.0
            - timestamp: ISO format timestamp

        Raises:
            ValueError: If inputs invalid or API call fails
        """
        # Input validation
        if not isinstance(patient_id, int) or patient_id < 1:
            raise ValueError(f"Invalid patient_id: {patient_id}")
        if not proposed_diagnosis or not isinstance(proposed_diagnosis, str):
            raise ValueError("proposed_diagnosis must be non-empty string")
        if not proposed_prescription or not isinstance(proposed_prescription, str):
            raise ValueError("proposed_prescription must be non-empty string")

        # Build patient context
        patient_context = self._build_patient_context(patient_id, db_manager)

        # Build clinical assessment prompt
        clinical_prompt = self._build_clinical_prompt(
            patient_context,
            proposed_diagnosis,
            proposed_prescription
        )

        # Call Claude Opus 4.6 with adaptive thinking
        suggestion = self._call_claude_analyzer(clinical_prompt)

        # Add metadata
        suggestion["analyzed_at"] = datetime.now().isoformat()
        suggestion["patient_id"] = patient_id
        suggestion["proposed_diagnosis"] = proposed_diagnosis
        suggestion["proposed_prescription"] = proposed_prescription

        return suggestion

    def _build_patient_context(
        self,
        patient_id: int,
        db_manager: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Build comprehensive patient context from database.

        Fetches: demographics, blood group, allergies, medical history, recent vitals.
        Falls back gracefully if data unavailable.

        Args:
            patient_id: Patient ID
            db_manager: DatabaseManager instance or None

        Returns:
            Dict with patient profile data
        """
        context = {
            "patient_id": patient_id,
            "demographics": {},
            "medical_history": [],
            "vitals": {},
            "current_medications": [],
            "allergies": []
        }

        if not db_manager:
            return context

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get patient demographics
                cursor.execute("""
                    SELECT patient_id, name, dob, gender, blood_group
                    FROM patients
                    WHERE patient_id = ?
                """, (patient_id,))
                patient = cursor.fetchone()

                if patient:
                    context["demographics"] = {
                        "name": patient[1],
                        "age": self._calculate_age(patient[2]),  # dob
                        "gender": patient[3],
                        "blood_group": patient[4],
                    }

                # Get medical history (last 10 visits)
                cursor.execute("""
                    SELECT record_id, patient_id, doctor_id, visit_date, diagnosis, prescription, notes
                    FROM medical_records
                    WHERE patient_id = ?
                    ORDER BY visit_date DESC
                    LIMIT 10
                """, (patient_id,))
                records = cursor.fetchall()

                for record in records:
                    context["medical_history"].append({
                        "visit_date": record[3],
                        "diagnosis": record[4],
                        "prescription": record[5],
                        "notes": record[6]
                    })

                # Parse vitals from recent medical notes
                if records and records[0][6]:  # Most recent notes field
                    vitals = self._parse_vitals_from_notes(records[0][6])
                    context["vitals"] = vitals

                # Extract current medications from prescription
                if records:
                    meds = self._extract_medications(records[0][5])  # prescription
                    context["current_medications"] = meds

        except Exception as e:
            # Gracefully degrade if DB access fails
            print(f"Warning: Could not fetch full patient data: {e}")
            # Continue with partial context

        return context

    def _calculate_age(self, dob_str: str) -> int:
        """Calculate patient age from DOB string (YYYY-MM-DD)."""
        try:
            from datetime import datetime
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return max(0, age)
        except:
            return 0

    def _parse_vitals_from_notes(self, notes: str) -> Dict[str, str]:
        """
        Extract vital signs from clinical notes using regex patterns.

        Looks for patterns like:
        - BP: 120/80, BP 120/80
        - HR: 72, Heart Rate: 72
        - Temp: 98.6, Temperature: 98.6
        - O2: 98%, SPO2: 98%
        """
        vitals = {}

        # Blood pressure: BP 120/80 or BP: 120/80
        bp_match = re.search(r'BP\s*:?\s*(\d{2,3})/(\d{2,3})', notes, re.IGNORECASE)
        if bp_match:
            vitals["blood_pressure"] = f"{bp_match.group(1)}/{bp_match.group(2)} mmHg"

        # Heart rate: HR 72 or HR: 72
        hr_match = re.search(r'HR\s*:?\s*(\d{2,3})\s*(?:bpm)?', notes, re.IGNORECASE)
        if hr_match:
            vitals["heart_rate"] = f"{hr_match.group(1)} bpm"

        # Temperature: Temp 98.6 or Temperature: 98.6
        temp_match = re.search(r'(?:Temp|Temperature)\s*:?\s*(\d{2}\.\d|\d{2})\s*(?:°F|F)?', notes, re.IGNORECASE)
        if temp_match:
            vitals["temperature"] = f"{temp_match.group(1)}°F"

        # Oxygen saturation: O2 98% or SPO2: 98%
        o2_match = re.search(r'(?:O2|SPO2|SpO2)\s*:?\s*(\d{2})\s*%?', notes, re.IGNORECASE)
        if o2_match:
            vitals["oxygen_saturation"] = f"{o2_match.group(1)}%"

        return vitals

    def _extract_medications(self, prescription: str) -> list:
        """
        Extract individual medications from prescription text.

        Attempts to parse common medication formats:
        - "Metformin 500mg daily"
        - "Drug1, Drug2, Drug3"
        - Multi-line prescriptions
        """
        if not prescription:
            return []

        meds = []
        # Split by comma or newline
        parts = re.split(r'[,\n]', prescription)
        for part in parts:
            part = part.strip()
            if part and len(part) > 2:  # Filter out noise
                # Extract drug name (first word before dosage/frequency)
                drug_name = re.match(r'^([A-Za-z\s]+)', part)
                if drug_name:
                    meds.append(drug_name.group(1).strip())

        return meds

    def _build_clinical_prompt(
        self,
        patient_context: Dict[str, Any],
        proposed_diagnosis: str,
        proposed_prescription: str
    ) -> str:
        """
        Build structured prompt for Claude clinical analysis.

        Includes patient context, proposed diagnosis/prescription, and analysis requirements.
        """
        medical_history_text = ""
        if patient_context.get("medical_history"):
            medical_history_text = "\n".join([
                f"- {rec['visit_date']}: {rec['diagnosis']} (Rx: {rec['prescription']})"
                for rec in patient_context["medical_history"][:5]  # Last 5 visits
            ])

        vitals_text = ""
        if patient_context.get("vitals"):
            vitals_text = ", ".join([
                f"{k}: {v}"
                for k, v in patient_context["vitals"].items()
            ])

        meds_text = ""
        if patient_context.get("current_medications"):
            meds_text = ", ".join(patient_context["current_medications"])

        demographics_text = ""
        if patient_context.get("demographics"):
            demo = patient_context["demographics"]
            demographics_text = f"Age: {demo.get('age', '?')}, Gender: {demo.get('gender', '?')}, Blood Group: {demo.get('blood_group', '?')}"

        prompt = f"""You are a clinical decision support AI assistant for a hospital management system.

PATIENT PROFILE:
{demographics_text}

Recent Vitals:
{vitals_text or 'No vitals recorded'}

Medical History (last 5 visits):
{medical_history_text or 'No prior records'}

Current Medications:
{meds_text or 'None recorded'}

PROPOSED DIAGNOSIS: {proposed_diagnosis}
PROPOSED PRESCRIPTION: {proposed_prescription}

ANALYSIS REQUIRED:
1. Is the proposed diagnosis consistent with patient demographics, vitals, and medical history?
2. Are there any drug-drug interactions or contraindications with current medications?
3. Are there any drug-allergy considerations for this patient?
4. What are the latest clinical guidelines for managing {proposed_diagnosis}?
5. Identify any high-risk combinations or safety concerns.
6. Overall risk assessment of this diagnosis/prescription combination.

Provide your analysis in the following JSON format:
{{
    "diagnosis_assessment": "Assessment of diagnosis consistency with patient context",
    "contraindications": ["List of", "drug interactions/contraindications found"],
    "clinical_concerns": ["List of", "clinical red flags or concerns"],
    "guideline_references": "Relevant clinical guidelines and best practices",
    "risk_level": "low|moderate|high|critical",
    "recommendations": ["Recommended", "follow-up actions"],
    "confidence": 0.95
}}

IMPORTANT:
- Be conservative and flag all potential concerns for patient safety
- Always recommend human clinical judgment as final authority
- Include specific drug names in contraindications
- Reference current clinical guidelines where applicable
- Return ONLY valid JSON, no additional text"""

        return prompt

    def _call_claude_analyzer(self, clinical_prompt: str) -> Dict[str, Any]:
        """
        Call Claude Opus 4.6 with adaptive thinking for clinical analysis.

        Uses streaming with .stream() context manager to properly parse response.

        Args:
            clinical_prompt: Formatted clinical analysis prompt

        Returns:
            Parsed JSON suggestion from Claude

        Raises:
            ValueError: If Claude response is invalid JSON or API fails
        """
        try:
            # Use streaming context manager to properly parse the response
            response_text = ""

            with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2000,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": clinical_prompt}]
            ) as stream:
                # Collect text from text_stream iterator
                for text in stream.text_stream:
                    response_text += text

            if not response_text:
                raise ValueError("Claude returned empty response")

            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise ValueError(f"No JSON found in response: {response_text[:300]}")

            suggestion = json.loads(json_match.group())

            # Validate required fields
            required_fields = [
                "diagnosis_assessment",
                "contraindications",
                "clinical_concerns",
                "guideline_references",
                "risk_level",
                "recommendations",
                "confidence"
            ]

            for field in required_fields:
                if field not in suggestion:
                    suggestion[field] = None

            return suggestion

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Claude's JSON response: {e}")
        except anthropic.APIError as e:
            raise ValueError(f"Claude API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error calling Claude API: {str(e)}")

    def get_suggestion_summary(self, suggestion: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of clinical suggestion.

        Args:
            suggestion: Suggestion dict from analyze_diagnosis()

        Returns:
            Formatted text summary
        """
        summary = []
        summary.append(f"Risk Level: {suggestion.get('risk_level', 'UNKNOWN').upper()}")

        if suggestion.get("diagnosis_assessment"):
            summary.append(f"\nDiagnosis Assessment:\n{suggestion['diagnosis_assessment']}")

        if suggestion.get("contraindications"):
            contraindications = suggestion["contraindications"]
            if contraindications:
                summary.append(f"\n⚠️  Contraindications:\n" + "\n".join([f"  - {c}" for c in contraindications]))

        if suggestion.get("clinical_concerns"):
            concerns = suggestion["clinical_concerns"]
            if concerns:
                summary.append(f"\n⚠️  Clinical Concerns:\n" + "\n".join([f"  - {c}" for c in concerns]))

        if suggestion.get("guideline_references"):
            summary.append(f"\nGuideline References:\n{suggestion['guideline_references']}")

        if suggestion.get("recommendations"):
            recommendations = suggestion["recommendations"]
            if recommendations:
                summary.append(f"\n✓ Recommendations:\n" + "\n".join([f"  - {r}" for r in recommendations]))

        summary.append(f"\nConfidence: {suggestion.get('confidence', 0):.1%}")

        return "\n".join(summary)



class ClinicalDecisionSupport:
    """
    Clinical decision support using Claude Opus 4.6 with adaptive thinking.

    Validates proposed diagnoses and prescriptions against:
    - Patient demographics, vitals, and medical history
    - Drug interactions and contraindications
    - Current clinical guidelines

    Returns structured suggestions with risk assessment (advisory only).
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize Clinical Decision Support.

        Args:
            anthropic_api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        """
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    def analyze_diagnosis(
        self,
        patient_id: int,
        proposed_diagnosis: str,
        proposed_prescription: str,
        db_manager: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze proposed diagnosis and prescription against patient profile.

        Args:
            patient_id: Patient ID from HMS database
            proposed_diagnosis: Proposed diagnosis text (e.g., "Type 2 Diabetes")
            proposed_prescription: Proposed prescription (e.g., "Metformin 500mg daily")
            db_manager: DatabaseManager instance to fetch patient data.
                       If None, uses minimal patient context.

        Returns:
            Structured suggestion dict with:
            - diagnosis_assessment: Consistency check
            - contraindications: List of drug interactions/allergies
            - clinical_concerns: List of clinical red flags
            - guideline_references: Relevant clinical guidelines
            - risk_level: low|moderate|high|critical
            - recommendations: Suggested actions
            - confidence: 0.0-1.0
            - timestamp: ISO format timestamp

        Raises:
            ValueError: If inputs invalid or API call fails
        """
        # Input validation
        if not isinstance(patient_id, int) or patient_id < 1:
            raise ValueError(f"Invalid patient_id: {patient_id}")
        if not proposed_diagnosis or not isinstance(proposed_diagnosis, str):
            raise ValueError("proposed_diagnosis must be non-empty string")
        if not proposed_prescription or not isinstance(proposed_prescription, str):
            raise ValueError("proposed_prescription must be non-empty string")

        # Build patient context
        patient_context = self._build_patient_context(patient_id, db_manager)

        # Build clinical assessment prompt
        clinical_prompt = self._build_clinical_prompt(
            patient_context,
            proposed_diagnosis,
            proposed_prescription
        )

        # Call Claude Opus 4.6 with adaptive thinking
        suggestion = self._call_claude_analyzer(clinical_prompt)

        # Add metadata
        suggestion["analyzed_at"] = datetime.now().isoformat()
        suggestion["patient_id"] = patient_id
        suggestion["proposed_diagnosis"] = proposed_diagnosis
        suggestion["proposed_prescription"] = proposed_prescription

        return suggestion

    def _build_patient_context(
        self,
        patient_id: int,
        db_manager: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Build comprehensive patient context from database.

        Fetches: demographics, blood group, allergies, medical history, recent vitals.
        Falls back gracefully if data unavailable.

        Args:
            patient_id: Patient ID
            db_manager: DatabaseManager instance or None

        Returns:
            Dict with patient profile data
        """
        context = {
            "patient_id": patient_id,
            "demographics": {},
            "medical_history": [],
            "vitals": {},
            "current_medications": [],
            "allergies": []
        }

        if not db_manager:
            return context

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get patient demographics
                cursor.execute("""
                    SELECT patient_id, name, dob, gender, blood_group
                    FROM patients
                    WHERE patient_id = ?
                """, (patient_id,))
                patient = cursor.fetchone()

                if patient:
                    context["demographics"] = {
                        "name": patient[1],
                        "age": self._calculate_age(patient[2]),  # dob
                        "gender": patient[3],
                        "blood_group": patient[4],
                    }

                # Get medical history (last 10 visits)
                cursor.execute("""
                    SELECT record_id, patient_id, doctor_id, visit_date, diagnosis, prescription, notes
                    FROM medical_records
                    WHERE patient_id = ?
                    ORDER BY visit_date DESC
                    LIMIT 10
                """, (patient_id,))
                records = cursor.fetchall()

                for record in records:
                    context["medical_history"].append({
                        "visit_date": record[3],
                        "diagnosis": record[4],
                        "prescription": record[5],
                        "notes": record[6]
                    })

                # Parse vitals from recent medical notes
                if records and records[0][6]:  # Most recent notes field
                    vitals = self._parse_vitals_from_notes(records[0][6])
                    context["vitals"] = vitals

                # Extract current medications from prescription
                if records:
                    meds = self._extract_medications(records[0][5])  # prescription
                    context["current_medications"] = meds

        except Exception as e:
            # Gracefully degrade if DB access fails
            print(f"Warning: Could not fetch full patient data: {e}")
            # Continue with partial context

        return context

    def _calculate_age(self, dob_str: str) -> int:
        """Calculate patient age from DOB string (YYYY-MM-DD)."""
        try:
            from datetime import datetime
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return max(0, age)
        except:
            return 0

    def _parse_vitals_from_notes(self, notes: str) -> Dict[str, str]:
        """
        Extract vital signs from clinical notes using regex patterns.

        Looks for patterns like:
        - BP: 120/80, BP 120/80
        - HR: 72, Heart Rate: 72
        - Temp: 98.6, Temperature: 98.6
        - O2: 98%, SPO2: 98%
        """
        vitals = {}

        # Blood pressure: BP 120/80 or BP: 120/80
        bp_match = re.search(r'BP\s*:?\s*(\d{2,3})/(\d{2,3})', notes, re.IGNORECASE)
        if bp_match:
            vitals["blood_pressure"] = f"{bp_match.group(1)}/{bp_match.group(2)} mmHg"

        # Heart rate: HR 72 or HR: 72
        hr_match = re.search(r'HR\s*:?\s*(\d{2,3})\s*(?:bpm)?', notes, re.IGNORECASE)
        if hr_match:
            vitals["heart_rate"] = f"{hr_match.group(1)} bpm"

        # Temperature: Temp 98.6 or Temperature: 98.6
        temp_match = re.search(r'(?:Temp|Temperature)\s*:?\s*(\d{2}\.\d|\d{2})\s*(?:°F|F)?', notes, re.IGNORECASE)
        if temp_match:
            vitals["temperature"] = f"{temp_match.group(1)}°F"

        # Oxygen saturation: O2 98% or SPO2: 98%
        o2_match = re.search(r'(?:O2|SPO2|SpO2)\s*:?\s*(\d{2})\s*%?', notes, re.IGNORECASE)
        if o2_match:
            vitals["oxygen_saturation"] = f"{o2_match.group(1)}%"

        return vitals

    def _extract_medications(self, prescription: str) -> list:
        """
        Extract individual medications from prescription text.

        Attempts to parse common medication formats:
        - "Metformin 500mg daily"
        - "Drug1, Drug2, Drug3"
        - Multi-line prescriptions
        """
        if not prescription:
            return []

        meds = []
        # Split by comma or newline
        parts = re.split(r'[,\n]', prescription)
        for part in parts:
            part = part.strip()
            if part and len(part) > 2:  # Filter out noise
                # Extract drug name (first word before dosage/frequency)
                drug_name = re.match(r'^([A-Za-z\s]+)', part)
                if drug_name:
                    meds.append(drug_name.group(1).strip())

        return meds

    def _build_clinical_prompt(
        self,
        patient_context: Dict[str, Any],
        proposed_diagnosis: str,
        proposed_prescription: str
    ) -> str:
        """
        Build structured prompt for Claude clinical analysis.

        Includes patient context, proposed diagnosis/prescription, and analysis requirements.
        """
        medical_history_text = ""
        if patient_context.get("medical_history"):
            medical_history_text = "\n".join([
                f"- {rec['visit_date']}: {rec['diagnosis']} (Rx: {rec['prescription']})"
                for rec in patient_context["medical_history"][:5]  # Last 5 visits
            ])

        vitals_text = ""
        if patient_context.get("vitals"):
            vitals_text = ", ".join([
                f"{k}: {v}"
                for k, v in patient_context["vitals"].items()
            ])

        meds_text = ""
        if patient_context.get("current_medications"):
            meds_text = ", ".join(patient_context["current_medications"])

        demographics_text = ""
        if patient_context.get("demographics"):
            demo = patient_context["demographics"]
            demographics_text = f"Age: {demo.get('age', '?')}, Gender: {demo.get('gender', '?')}, Blood Group: {demo.get('blood_group', '?')}"

        prompt = f"""You are a clinical decision support AI assistant for a hospital management system.

PATIENT PROFILE:
{demographics_text}

Recent Vitals:
{vitals_text or 'No vitals recorded'}

Medical History (last 5 visits):
{medical_history_text or 'No prior records'}

Current Medications:
{meds_text or 'None recorded'}

PROPOSED DIAGNOSIS: {proposed_diagnosis}
PROPOSED PRESCRIPTION: {proposed_prescription}

ANALYSIS REQUIRED:
1. Is the proposed diagnosis consistent with patient demographics, vitals, and medical history?
2. Are there any drug-drug interactions or contraindications with current medications?
3. Are there any drug-allergy considerations for this patient?
4. What are the latest clinical guidelines for managing {proposed_diagnosis}?
5. Identify any high-risk combinations or safety concerns.
6. Overall risk assessment of this diagnosis/prescription combination.

Provide your analysis in the following JSON format:
{{
    "diagnosis_assessment": "Assessment of diagnosis consistency with patient context",
    "contraindications": ["List of", "drug interactions/contraindications found"],
    "clinical_concerns": ["List of", "clinical red flags or concerns"],
    "guideline_references": "Relevant clinical guidelines and best practices",
    "risk_level": "low|moderate|high|critical",
    "recommendations": ["Recommended", "follow-up actions"],
    "confidence": 0.95
}}

IMPORTANT:
- Be conservative and flag all potential concerns for patient safety
- Always recommend human clinical judgment as final authority
- Include specific drug names in contraindications
- Reference current clinical guidelines where applicable
- Return ONLY valid JSON, no additional text"""

        return prompt

    def _call_claude_analyzer(self, clinical_prompt: str) -> Dict[str, Any]:
        """
        Call Claude Opus 4.6 with adaptive thinking for clinical analysis.

        Uses adaptive thinking for medical accuracy.

        Args:
            clinical_prompt: Formatted clinical analysis prompt

        Returns:
            Parsed JSON suggestion from Claude

        Raises:
            ValueError: If Claude response is invalid JSON or API fails
        """
        try:
            # Call Claude with streaming to properly get the final message
            response_text = ""
            with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2000,
                thinking={
                    "type": "adaptive"
                },
                messages=[
                    {
                        "role": "user",
                        "content": clinical_prompt
                    }
                ]
            ) as stream:
                # Collect all text from streaming response
                for text in stream.text_stream:
                    response_text += text

            if not response_text:
                raise ValueError("Claude returned empty response. Check API key and model availability.")

            # Parse JSON from response
            # Extract JSON object from response (handles whitespace/markdown)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise ValueError(f"No JSON found in Claude response: {response_text[:300]}")

            suggestion = json.loads(json_match.group())

            # Validate required fields
            required_fields = [
                "diagnosis_assessment",
                "contraindications",
                "clinical_concerns",
                "guideline_references",
                "risk_level",
                "recommendations",
                "confidence"
            ]

            for field in required_fields:
                if field not in suggestion:
                    suggestion[field] = None

            return suggestion

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Claude's JSON response: {e}")
        except anthropic.APIError as e:
            raise ValueError(f"Claude API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error calling Claude API: {str(e)}")

    def get_suggestion_summary(self, suggestion: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of clinical suggestion.

        Args:
            suggestion: Suggestion dict from analyze_diagnosis()

        Returns:
            Formatted text summary
        """
        summary = []
        summary.append(f"Risk Level: {suggestion.get('risk_level', 'UNKNOWN').upper()}")

        if suggestion.get("diagnosis_assessment"):
            summary.append(f"\nDiagnosis Assessment:\n{suggestion['diagnosis_assessment']}")

        if suggestion.get("contraindications"):
            contraindications = suggestion["contraindications"]
            if contraindications:
                summary.append(f"\n⚠️  Contraindications:\n" + "\n".join([f"  - {c}" for c in contraindications]))

        if suggestion.get("clinical_concerns"):
            concerns = suggestion["clinical_concerns"]
            if concerns:
                summary.append(f"\n⚠️  Clinical Concerns:\n" + "\n".join([f"  - {c}" for c in concerns]))

        if suggestion.get("guideline_references"):
            summary.append(f"\nGuideline References:\n{suggestion['guideline_references']}")

        if suggestion.get("recommendations"):
            recommendations = suggestion["recommendations"]
            if recommendations:
                summary.append(f"\n✓ Recommendations:\n" + "\n".join([f"  - {r}" for r in recommendations]))

        summary.append(f"\nConfidence: {suggestion.get('confidence', 0):.1%}")

        return "\n".join(summary)
