# Ambient AI Scribe Module - Setup & Usage Guide

## Overview

The Ambient AI Scribe is an intelligent module that records doctor-patient conversations and automatically generates:
- **SOAP Notes** (Subjective, Objective, Assessment, Plan)
- **Prescriptions** with dosage and frequency
- **Billing Codes** (ICD-10 and CPT)
- **Drug Interaction Alerts** (real-time during visit)

All data is automatically saved to the HMS database.

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install SpeechRecognition pydub
```

**Optional**: For microphone support (real recording):
```bash
pip install pyaudio
```

For MacOS:
```bash
brew install portaudio
pip install pyaudio
```

### 2. Initialize Database with Drug Data

```python
from database import DatabaseManager

db = DatabaseManager("hms_database.db")
db.create_tables()
db.seed_data()
db.seed_drug_data()  # Populates drug interactions & billing codes
```

---

## Quick Start

### Basic Usage (Mock Mode - No Microphone Needed)

```python
from database import DatabaseManager
from ambient_scribe.scribe_session import ScribeSession

# Initialize database
db = DatabaseManager("hms_database.db")

# Create scribe session
scribe = ScribeSession(
    db_manager=db,
    patient_id=1,
    doctor_id=1,
    appointment_id=1,
    use_mock=True  # Use mock data for testing
)

# Record conversation (or load mock transcript)
scribe.record_conversation(sample_type="cardiology")

# Analyze and generate SOAP note
scribe.generate_clinical_note()

# Generate prescriptions
scribe.generate_prescriptions()

# Check drug interactions
scribe.flag_drug_interactions()

# Generate billing codes
scribe.generate_billing_codes()

# Save everything to database
scribe.complete_session()

# Display summary
print(scribe.get_session_summary())
```

### Real Microphone Recording

```python
scribe = ScribeSession(
    db_manager=db,
    patient_id=1,
    doctor_id=1,
    use_mock=False  # Use real microphone
)

# Records for 120 seconds
scribe.record_conversation(duration_seconds=120)
```

---

## Module Components

### 1. AudioRecorder
Records doctor-patient conversations using SpeechRecognition library.

```python
from ambient_scribe.audio_recorder import AudioRecorder

recorder = AudioRecorder(use_mock=True)
recorder.load_mock_transcript("cardiology")  # Load sample
transcript = recorder.get_transcript()
```

**Mock Samples Available:**
- `"default"` - General checkup
- `"cardiology"` - Chest pain evaluation
- `"orthopedics"` - Knee injury assessment

### 2. ConversationAnalyzer
Extracts clinical information using regex and keyword matching.

```python
from ambient_scribe.conversation_analyzer import ConversationAnalyzer

analyzer = ConversationAnalyzer()
clinical_data = analyzer.extract_clinical_data(transcript_text)

# Returns: {
#   'chief_complaint': '...',
#   'symptoms': [...],
#   'vital_signs': {...},
#   'conditions': [...],
#   'medications': [...],
#   'allergies': [...],
#   'assessment': '...',
#   'plan': [...]
# }
```

### 3. SOAPNoteGenerator
Generates formatted SOAP notes from clinical data.

```python
from ambient_scribe.soap_generator import SOAPNoteGenerator

generator = SOAPNoteGenerator()
soap = generator.generate(clinical_data)

# Save to medical records
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medical_records
        (patient_id, doctor_id, visit_date, notes)
        VALUES (?, ?, ?, ?)
    """, (patient_id, doctor_id, datetime.now(), soap.to_formatted_text()))
```

### 4. PrescriptionGenerator
Generates prescriptions using diagnosis-to-drug mapping.

```python
from ambient_scribe.prescription_generator import PrescriptionGenerator

generator = PrescriptionGenerator()
prescriptions = generator.generate(clinical_data)

for rx in prescriptions:
    print(f"{rx.drug_name} {rx.dosage} {rx.frequency}")
```

### 5. DrugInteractionChecker
Real-time drug interaction detection.

```python
from ambient_scribe.drug_interaction_checker import DrugInteractionChecker

checker = DrugInteractionChecker(db_manager=db)

drugs = ["aspirin", "metoprolol"]
interactions = checker.check_interactions(drugs)

if interactions:
    print(checker.display_interactions(interactions))
```

**Severity Levels:**
- `'warning'` - Minor interaction, monitor
- `'alert'` - Significant interaction, consider alternative
- `'critical'` - Severe interaction, avoid combination

### 6. BillingCodeGenerator
Maps diagnoses to medical billing codes.

```python
from ambient_scribe.billing_code_generator import BillingCodeGenerator

generator = BillingCodeGenerator(db_manager=db)
codes = generator.generate(clinical_data)

# codes contain: ICD-10 (diagnosis) + CPT (visit complexity)
for code in codes:
    print(f"{code.code} ({code.code_type}): {code.description}")
```

### 7. ScribeSession
Main orchestrator tying all components together.

```python
from ambient_scribe.scribe_session import ScribeSession

scribe = ScribeSession(db_manager, patient_id, doctor_id)

# Full workflow
scribe.record_conversation()
scribe.generate_clinical_note()
scribe.generate_prescriptions()
scribe.flag_drug_interactions()
scribe.generate_billing_codes()
scribe.complete_session()  # Saves everything
```

---

## Workflow & Data Flow

```
Doctor-Patient Conversation (Recorded)
        ↓
    [AudioRecorder]
        ↓
    Transcript Text
        ↓
    [ConversationAnalyzer] → Extract clinical data
        ↓
    Structured Data Dictionary
        ↓
    ├─→ [SOAPNoteGenerator] → SOAP Note ↓ Save to medical_records.notes
    ├─→ [PrescriptionGenerator] → Prescriptions ↓ Save to medical_records.prescription
    ├─→ [DrugInteractionChecker] → Interactions ↓ Display warnings
    └─→ [BillingCodeGenerator] → Billing Codes ↓ Save to billing table
        ↓
    [ScribeSession.complete_session()]
        ↓
    ✅ All data saved to HMS database
```

---

## Database Schema Extensions

The module adds/modifies these tables:

### Modified: `billing`
```sql
ALTER TABLE billing ADD COLUMN billing_code TEXT;
ALTER TABLE billing ADD COLUMN description TEXT;
```

### New: `drug_interactions`
```sql
CREATE TABLE drug_interactions (
    interaction_id INTEGER PRIMARY KEY,
    drug1 TEXT,
    drug2 TEXT,
    severity TEXT,  -- 'warning', 'alert', 'critical'
    description TEXT
);
```

### New: `billing_codes`
```sql
CREATE TABLE billing_codes (
    code_id INTEGER PRIMARY KEY,
    code TEXT,                -- ICD-10 or CPT
    code_type TEXT,           -- 'ICD-10' or 'CPT'
    description TEXT,
    standard_amount DECIMAL,
    category TEXT
);
```

---

## Real-Time Drug Interaction Alerts

The system checks for interactions **during the visit** as medications are prescribed:

```python
# During recording/processing
interactions = drug_checker.check_interactions(['aspirin', 'metoprolol'])

if interactions:
    for interaction in interactions:
        if interaction.severity == 'critical':
            print(f"🛑 CRITICAL: {interaction.display_message()}")
        elif interaction.severity == 'alert':
            print(f"🚨 ALERT: {interaction.display_message()}")
```

---

## Running Examples

### Full Demo
```bash
python examples/example_scribe_usage.py --demo full
```

### Multiple Scenarios
```bash
python examples/example_scribe_usage.py --demo scenarios
```

### Live Recording (requires microphone)
```bash
python examples/example_scribe_usage.py --demo real
```

---

## Features & Capabilities

### ✅ What It Does

- **Automatic Documentation**: Generates professional SOAP notes from conversation
- **Prescription Management**: Creates prescriptions with dosage and frequency
- **Drug Safety**: Real-time interaction checking and warnings
- **Medical Coding**: ICD-10 and CPT billing code generation
- **Database Integration**: Seamless saving to HMS medical records and billing
- **Mock Mode**: Full testing without microphone/recording equipment
- **Audit Trail**: Complete logging of all operations

### ⚠️ Current Limitations

- Template-based (not AI/LLM-based)
- Regex pattern matching for extraction (rule-based)
- Limited drug database (~15 sample interactions)
- Simplified diagnosis-to-drug mapping
- Mock mode available for demonstration

### 🔄 Can Be Extended With

- Integration with Anthropic Claude API for advanced note generation
- Real drug interaction database (FDA database)
- HL7/FHIR compliance for healthcare interoperability
- Multi-language support
- Custom drug and billing code databases

---

## Troubleshooting

### SpeechRecognition Not Available
```
Error: SpeechRecognition not installed
Solution: pip install SpeechRecognition pydub
```

### Microphone Not Detected
```
Use mock mode: use_mock=True in ScribeSession
Or install pyaudio: pip install pyaudio
```

### No Drug Interactions in Database
```
Make sure to call: db.seed_drug_data()
Verify: SELECT COUNT(*) FROM drug_interactions;
```

### Medical Record Not Saving
```
Check: 1. Patient ID exists
       2. Doctor ID exists
       3. Database connection is active
       4. Foreign key constraints enabled
```

---

## API Reference

### ScribeSession Methods

| Method | Description |
|--------|-------------|
| `record_conversation(duration_seconds, sample_type)` | Record/load conversation |
| `generate_clinical_note()` | Generate SOAP note |
| `generate_prescriptions()` | Generate medications |
| `flag_drug_interactions()` | Check for interactions |
| `generate_billing_codes()` | Generate medical codes |
| `save_to_medical_record()` | Save note to database |
| `create_billing_entries()` | Create bill records |
| `complete_session()` | Run entire workflow |
| `get_session_summary()` | Display session overview |

### Session Object Properties

```python
scribe.session.transcript       # Transcript object
scribe.session.soap_note        # SOAPNote object
scribe.session.prescriptions    # List[PrescriptionItem]
scribe.session.drug_interactions # List[DrugInteraction]
scribe.session.billing_codes    # List[BillingCode]
scribe.session.clinical_data    # Dict of extracted data
scribe.session.warnings         # List of warnings
scribe.session.errors           # List of errors
```

---

## License & Compliance

This module is designed for:
- Hospital/clinic use with proper EMR integration
- Educational and research purposes
- Demonstration and prototyping

Ensure compliance with:
- HIPAA regulations (patient data privacy)
- Medical records documentation requirements
- Local healthcare system policies
- Audio recording consent laws

---

## Support & Documentation

For questions or issues:
1. Review examples in `examples/example_scribe_usage.py`
2. Check module docstrings
3. Review HMS database schema
4. Examine mock transcripts for expected formats

---

## Next Steps

1. **Install dependencies**: `pip install SpeechRecognition pydub`
2. **Run demo**: `python examples/example_scribe_usage.py --demo full`
3. **Review generated data**: Check HMS database for saved records
4. **Customize**: Modify drug maps, billing codes, or SOAP templates as needed
5. **Integrate**: Add to your HMS production workflow

---

## Version

- Ambient AI Scribe: v1.0.0
- Requires: Python 3.6+, HMS Database
- Created: 2026-03-28
