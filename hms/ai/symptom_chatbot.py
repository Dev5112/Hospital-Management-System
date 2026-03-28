"""
Symptom Triage Chatbot using Anthropic Claude API.
Multi-turn conversational triage with severity assessment.
"""

import sys
from typing import Dict, List, Any
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CHATBOT_CONFIG
from anthropic import Anthropic


class SymptomChatbot:
    """
    Multi-turn symptom triage chatbot powered by Claude.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize chatbot.

        Args:
            api_key: Anthropic API key
        """
        if api_key is None:
            api_key = ANTHROPIC_API_KEY

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL
        self.conversation_history = []
        self.turn_count = 0
        self.symptoms_collected = []
        self.severity_indicators = []

    def build_system_prompt(self) -> str:
        """Build system prompt for triage nurse."""
        return """You are a compassionate hospital triage nurse with 15 years of emergency experience. Your role is to:

1. Collect symptoms from the patient through natural, empathetic conversation
2. Ask one specific question at a time
3. Listen carefully and ask clarifying follow-up questions
4. Assess severity based on red flags
5. Determine appropriate department/triage level

Severity assessment guidelines:
- EMERGENT (Immediate): Chest pain, severe difficulty breathing, loss of consciousness, severe bleeding, signs of stroke
- URGENT (Within 1 hour): High fever (>39°C), severe pain, uncontrolled vomiting, moderate breathing issues
- SEMI-URGENT (Within 2 hours): Moderate symptoms, stable vitals
- NON-URGENT (Routine): Minor issues, non-emergency

Always be:
- Empathetic and reassuring
- Professional but friendly
- Focused on patient safety
- Clear about next steps

After 5-8 exchanges or when you have enough information, provide a structured triage assessment."""

    def call_claude(self, user_message: str) -> str:
        """
        Call Claude API for chat response.

        Args:
            user_message: User's message

        Returns:
            Claude's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=self.build_system_prompt(),
            messages=self.conversation_history,
            temperature=CHATBOT_CONFIG["temperature"]
        )

        assistant_message = response.content[0].text

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        self.turn_count += 1

        return assistant_message

    def extract_triage_assessment(self) -> dict:
        """
        Extract structured triage assessment from conversation.

        Returns:
            Dictionary with triage details
        """
        # Use Claude to extract structured assessment
        extraction_prompt = f"""Based on the patient conversation so far, provide a JSON triage assessment.

Conversation summary:
{self._get_conversation_summary()}

Provide ONLY valid JSON in this exact format:
{{
  "triage_priority": "Emergent|Urgent|Semi-Urgent|Non-Urgent",
  "recommended_department": "Emergency|Cardiology|Neurology|General|Orthopedic|Pediatrics|OB-GYN|Psychiatry|Other",
  "estimated_wait_minutes": <number>,
  "preliminary_concern": "<brief primary concern>",
  "instructions": "<what to do before being seen>",
  "follow_up_required": true|false
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.3
        )

        import json
        try:
            assessment_text = response.content[0].text
            # Extract JSON from response
            json_start = assessment_text.find("{")
            json_end = assessment_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                assessment = json.loads(assessment_text[json_start:json_end])
            else:
                assessment = self._default_assessment()
        except:
            assessment = self._default_assessment()

        return assessment

    def _get_conversation_summary(self) -> str:
        """Get summary of conversation so far."""
        summary = ""
        for msg in self.conversation_history:
            role_label = "Patient" if msg["role"] == "user" else "Nurse"
            summary += f"{role_label}: {msg['content'][:100]}...\n"
        return summary

    def _default_assessment(self) -> dict:
        """Provide default assessment."""
        return {
            "triage_priority": "Semi-Urgent",
            "recommended_department": "General",
            "estimated_wait_minutes": 30,
            "preliminary_concern": "Requires in-person evaluation",
            "instructions": "Please check in at the front desk",
            "follow_up_required": False
        }

    def run(self, initial_message: str = None) -> dict:
        """
        Run chatbot session.

        Args:
            initial_message: Optional initial patient message

        Returns:
            Final assessment dictionary
        """
        if initial_message is None:
            initial_message = "Hello, I don't feel well."

        print("=== Hospital Symptom Triage Chatbot ===\n")
        print("Type 'done' or 'exit' to end the conversation and get assessment.\n")

        # Greeting
        greeting = self.call_claude(initial_message)
        print(f"Nurse: {greeting}\n")

        # Conversation loop
        max_turns = CHATBOT_CONFIG["max_turns"]
        auto_summary_after = CHATBOT_CONFIG["auto_summary_after_turns"]

        while self.turn_count < max_turns:
            user_input = input("You: ").strip()

            if user_input.lower() in ["done", "exit", "quit"]:
                break

            if not user_input:
                continue

            # Get nurse response
            nurse_response = self.call_claude(user_input)
            print(f"\nNurse: {nurse_response}\n")

            # Auto-assess after sufficient turns
            if self.turn_count >= auto_summary_after and self.turn_count % auto_summary_after == 0:
                print("\n[Collecting information... Hold on for assessment]\n")

        # Extract and return assessment
        assessment = self.extract_triage_assessment()

        print("\n" + "="*50)
        print("TRIAGE ASSESSMENT")
        print("="*50)
        print(f"Priority Level: {assessment.get('triage_priority', 'Unknown')}")
        print(f"Recommended Department: {assessment.get('recommended_department', 'Unknown')}")
        print(f"Estimated Wait Time: {assessment.get('estimated_wait_minutes', 30)} minutes")
        print(f"Preliminary Concern: {assessment.get('preliminary_concern', 'To be determined')}")
        print(f"Instructions: {assessment.get('instructions', 'Check in at front desk')}")

        return assessment

    def run_single_turn(self, user_message: str) -> str:
        """
        Single turn interaction (for API use).

        Args:
            user_message: User's message

        Returns:
            Chatbot's response
        """
        return self.call_claude(user_message)


if __name__ == "__main__":
    """Demo: Run chatbot"""
    chatbot = SymptomChatbot()

    # Run demo conversation
    assessment = chatbot.run("I've had a fever and cough for 3 days")
