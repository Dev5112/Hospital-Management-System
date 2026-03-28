"""
Synthetic data generation for HMS AI/ML models.
Generates realistic medical data for training and testing.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()


def generate_patient_records(n: int = 5000) -> pd.DataFrame:
    """
    Generate synthetic patient records with realistic medical profiles.

    Args:
        n: Number of patient records to generate

    Returns:
        DataFrame with patient data
    """
    data = []

    for _ in range(n):
        # Age distribution (normal around 45)
        age = max(18, min(100, int(np.random.normal(45, 20))))

        # Gender
        gender = np.random.choice(["M", "F"])

        # Vitals (realistic ranges)
        systolic_bp = max(80, min(200, int(np.random.normal(130, 20))))
        diastolic_bp = max(60, min(130, int(np.random.normal(80, 15))))
        temperature = np.random.uniform(36.5, 37.5)
        heart_rate = max(40, min(120, int(np.random.normal(72, 15))))
        blood_glucose = max(60, min(300, int(np.random.normal(110, 40))))

        # BMI (realistic distribution)
        bmi = np.random.gamma(shape=2, scale=7) + 18
        bmi = max(16, min(50, bmi))

        # Lab results (normalized)
        wbc = np.random.gamma(shape=5, scale=2)  # White Blood Cells
        rbc = np.random.normal(4.7, 0.5)  # Red Blood Cells
        hemoglobin = np.random.normal(14, 2)

        # Symptoms (multiple per patient)
        all_symptoms = [
            "fever", "cough", "fatigue", "chest_pain", "headache",
            "dizziness", "nausea", "shortness_of_breath", "chills",
            "muscle_aches", "sore_throat", "congestion", "rash"
        ]
        n_symptoms = np.random.poisson(1.5)
        symptoms = list(np.random.choice(all_symptoms, min(n_symptoms, len(all_symptoms)), replace=False))

        # Comorbidities
        comorbidities = []
        if age > 40 and np.random.random() < 0.4:
            comorbidities.append("Hypertension")
        if age > 50 and np.random.random() < 0.3:
            comorbidities.append("Type 2 Diabetes")
        if np.random.random() < 0.2:
            comorbidities.append("Asthma")
        if np.random.random() < 0.15:
            comorbidities.append("High Cholesterol")

        data.append({
            "patient_id": fake.uuid4()[:8],
            "age": age,
            "gender": gender,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "temperature": round(temperature, 2),
            "heart_rate": heart_rate,
            "blood_glucose": blood_glucose,
            "bmi": round(bmi, 2),
            "wbc": round(wbc, 2),
            "rbc": round(rbc, 2),
            "hemoglobin": round(hemoglobin, 2),
            "symptoms": ";".join(symptoms) if symptoms else "none",
            "comorbidities": ";".join(comorbidities) if comorbidities else "none",
        })

    return pd.DataFrame(data)


def generate_appointment_records(n: int = 3000) -> pd.DataFrame:
    """
    Generate synthetic appointment records with no-show patterns.

    Args:
        n: Number of appointment records

    Returns:
        DataFrame with appointment data
    """
    data = []

    for _ in range(n):
        patient_age = max(18, min(100, int(np.random.normal(50, 25))))

        appointment_type = np.random.choice(
            ["routine", "follow-up", "specialist", "emergency"],
            p=[0.4, 0.35, 0.15, 0.1]
        )

        day_of_week = np.random.choice(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )

        time_of_day = np.random.choice(["morning", "afternoon", "evening"], p=[0.5, 0.35, 0.15])

        lead_time_days = max(1, int(np.random.exponential(10)))

        previous_no_shows = max(0, int(np.random.exponential(0.5)))

        previous_appointments = max(1, int(np.random.exponential(5)))

        distance_km = max(0.5, np.random.gamma(shape=2, scale=5))

        insurance_type = np.random.choice(["Private", "Government", "None"], p=[0.6, 0.35, 0.05])

        reminder_sent = np.random.choice([True, False], p=[0.7, 0.3])

        # No-show probability based on features
        no_show_prob = 0.3
        no_show_prob += 0.1 if previous_no_shows > 0 else 0
        no_show_prob += 0.05 if lead_time_days > 30 else 0
        no_show_prob += 0.05 if distance_km > 15 else 0
        no_show_prob -= 0.1 if reminder_sent else 0
        no_show_prob = max(0.0, min(1.0, no_show_prob))

        no_show = np.random.random() < no_show_prob

        appointment_date = fake.date_between(start_date="-90d", end_date="+30d")

        data.append({
            "appointment_id": fake.uuid4()[:8],
            "patient_age": patient_age,
            "appointment_type": appointment_type,
            "day_of_week": day_of_week,
            "time_of_day": time_of_day,
            "lead_time_days": lead_time_days,
            "previous_no_shows": previous_no_shows,
            "previous_appointments": previous_appointments,
            "distance_km": round(distance_km, 2),
            "insurance_type": insurance_type,
            "reminder_sent": reminder_sent,
            "no_show": no_show,
            "appointment_date": appointment_date,
        })

    return pd.DataFrame(data)


def generate_billing_records(n: int = 2000) -> pd.DataFrame:
    """
    Generate synthetic billing records with fraud patterns.

    Args:
        n: Number of billing records

    Returns:
        DataFrame with billing data
    """
    data = []

    for _ in range(n):
        bill_amount = max(500, np.random.gamma(shape=2, scale=2000))

        service_codes = np.random.choice(
            ["MRI", "CT_SCAN", "ECG", "LAB_WORK", "SURGERY", "CONSULTATION", "PHARMACY", "XRAY"],
            size=np.random.randint(1, 5)
        ).tolist()

        diagnosis_codes = np.random.choice(
            ["DIAB", "HTN", "CAD", "PNEU", "CKD", "ACS", "CHF", "AFIB"],
            size=np.random.randint(1, 3)
        ).tolist()

        num_services = len(service_codes)

        length_of_stay_days = max(1, int(np.random.exponential(3)))

        patient_age = max(18, min(100, int(np.random.normal(55, 25))))

        department = np.random.choice(["Cardiology", "Neurology", "General", "Orthopedic", "ICU"])

        # Expected average bill based on department
        dept_avg = {
            "Cardiology": 8000,
            "Neurology": 7000,
            "General": 4000,
            "Orthopedic": 6000,
            "ICU": 15000,
        }
        historical_avg_bill = dept_avg.get(department, 5000)

        # Add some normal variation
        historical_avg_bill += np.random.normal(0, historical_avg_bill * 0.1)

        deviation_from_avg = (bill_amount - historical_avg_bill) / historical_avg_bill if historical_avg_bill > 0 else 0

        # Fraud indicator: ~5% fraud rate
        # High deviation + multiple services + mismatched diagnosis/service
        fraud_score = 0
        if abs(deviation_from_avg) > 2:
            fraud_score += 0.4
        if num_services > 5:
            fraud_score += 0.3
        if len(service_codes) > len(diagnosis_codes) * 1.5:
            fraud_score += 0.3

        is_fraud = fraud_score > 0.5 or np.random.random() < 0.05

        data.append({
            "bill_id": fake.uuid4()[:8],
            "bill_amount": round(bill_amount, 2),
            "num_services": num_services,
            "service_codes": ";".join(service_codes),
            "diagnosis_codes": ";".join(diagnosis_codes),
            "length_of_stay_days": length_of_stay_days,
            "patient_age": patient_age,
            "department": department,
            "historical_avg_bill": round(historical_avg_bill, 2),
            "deviation_from_avg": round(deviation_from_avg, 3),
            "is_fraud": is_fraud,
        })

    return pd.DataFrame(data)


def generate_admission_records(n: int = 2000) -> pd.DataFrame:
    """
    Generate synthetic admission records with readmission risk patterns.

    Args:
        n: Number of admission records

    Returns:
        DataFrame with admission data
    """
    data = []

    for _ in range(n):
        age = max(18, min(100, int(np.random.normal(55, 25))))

        gender = np.random.choice(["M", "F"])

        diagnosis = np.random.choice([
            "Type 2 Diabetes", "Hypertension", "Pneumonia", "COVID-19",
            "Heart Disease", "Kidney Disease", "Stroke", "Cancer"
        ])

        num_previous_admissions = max(0, int(np.random.exponential(0.8)))

        length_of_stay = max(1, int(np.random.exponential(4)))

        comorbidities_list = []
        if age > 50 and np.random.random() < 0.5:
            comorbidities_list.append("Hypertension")
        if np.random.random() < 0.3:
            comorbidities_list.append("Diabetes")
        if np.random.random() < 0.2:
            comorbidities_list.append("COPD")

        medication_count = max(1, int(np.random.exponential(2)))

        medication_adherence = np.random.beta(2, 2)  # Concentration around 0.5

        discharge_disposition = np.random.choice(["home", "facility", "AMA"], p=[0.6, 0.3, 0.1])

        insurance_type = np.random.choice(["Private", "Government", "None"], p=[0.6, 0.35, 0.05])

        # Readmission risk calculation
        risk_score = 0
        if num_previous_admissions > 2:
            risk_score += 25
        if medication_adherence < 0.5:
            risk_score += 20
        if len(comorbidities_list) > 1:
            risk_score += 15
        if discharge_disposition != "home":
            risk_score += 10
        if age > 70:
            risk_score += 15

        risk_score = min(100, risk_score + np.random.normal(0, 10))

        readmission_within_30_days = np.random.random() < (risk_score / 100)

        data.append({
            "admission_id": fake.uuid4()[:8],
            "age": age,
            "gender": gender,
            "diagnosis": diagnosis,
            "num_previous_admissions": num_previous_admissions,
            "length_of_stay_days": length_of_stay,
            "comorbidities": ";".join(comorbidities_list) if comorbidities_list else "none",
            "medication_count": medication_count,
            "medication_adherence_score": round(medication_adherence, 2),
            "discharge_disposition": discharge_disposition,
            "insurance_type": insurance_type,
            "readmission_risk_score": round(risk_score, 1),
            "readmission_within_30_days": readmission_within_30_days,
        })

    return pd.DataFrame(data)


def generate_drug_pairs(n: int = 500) -> pd.DataFrame:
    """
    Generate synthetic drug interaction data.

    Args:
        n: Number of drug pairs

    Returns:
        DataFrame with drug interaction data
    """
    drugs = [
        "Metformin", "Aspirin", "Lisinopril", "Warfarin", "Amoxicillin",
        "Ibuprofen", "Omeprazole", "Amlodipine", "Simvastatin", "Atorvastatin",
        "Clopidogrel", "Paracetamol", "Albuterol", "Fluoxetine", "Sertraline",
        "Levothyroxine", "Losartan", "Enalapril", "Furosemide", "Hydrochlorothiazide",
    ]

    # Predefined severe interactions
    severe_interactions = [
        ("Warfarin", "Aspirin"),
        ("Warfarin", "NSAIDs"),
        ("ACE_Inhibitors", "Potassium_Supplements"),
        ("Metformin", "Contrast_Dye"),
    ]

    data = []

    for _ in range(n):
        if np.random.random() < 0.15 and severe_interactions:
            # Pick a severe interaction
            drug1, drug2 = random.choice(severe_interactions)
            severity = "Severe"
            effect = f"Critical interaction between {drug1} and {drug2}"
        elif np.random.random() < 0.3:
            # Moderate interaction
            drug1, drug2 = random.sample(drugs, 2)
            severity = "Moderate"
            effect = f"Decreased efficacy or increased side effects"
        else:
            # Safe or mild interaction
            drug1, drug2 = random.sample(drugs, 2)
            severity = np.random.choice(["Mild", "Safe"], p=[0.3, 0.7])
            effect = "No significant interaction" if severity == "Safe" else "Minor side effects possible"

        interacts = severity in ["Severe", "Moderate"]

        data.append({
            "drug_pair_id": fake.uuid4()[:8],
            "drug1": drug1,
            "drug2": drug2,
            "severity": severity,
            "effect": effect,
            "interacts": interacts,
        })

    return pd.DataFrame(data)


def generate_time_series_occupancy(days: int = 365) -> pd.DataFrame:
    """
    Generate synthetic bed occupancy time series data.

    Args:
        days: Number of days to generate

    Returns:
        DataFrame with daily occupancy data
    """
    data = []

    # Different patterns for different ward types
    ward_configs = {
        "general": {"base": 80, "seasonal_amp": 20, "noise": 5},
        "ICU": {"base": 18, "seasonal_amp": 5, "noise": 2},
        "private": {"base": 40, "seasonal_amp": 15, "noise": 3},
        "maternity": {"base": 30, "seasonal_amp": 10, "noise": 2},
    }

    start_date = datetime.now() - timedelta(days=days)

    for ward_type, config in ward_configs.items():
        for day in range(days):
            current_date = start_date + timedelta(days=day)

            # Seasonal pattern (sine wave)
            seasonal = config["seasonal_amp"] * np.sin(2 * np.pi * day / 365)

            # Trend
            trend = (day / days) * 5

            # Noise
            noise = np.random.normal(0, config["noise"])

            # Day-of-week effect (lower on weekends)
            dow_effect = -5 if current_date.weekday() >= 5 else 0

            occupancy = config["base"] + seasonal + trend + noise + dow_effect
            occupancy = max(1, int(occupancy))

            data.append({
                "ward_type": ward_type,
                "date": current_date.date(),
                "occupancy": occupancy,
            })

    return pd.DataFrame(data)


if __name__ == "__main__":
    """Demo: Generate and display sample synthetic data"""
    print("Generating synthetic patient records...")
    patients_df = generate_patient_records(100)
    print(f"Generated {len(patients_df)} patient records")
    print(patients_df.head())

    print("\nGenerating synthetic appointment records...")
    appointments_df = generate_appointment_records(100)
    print(f"Generated {len(appointments_df)} appointment records")
    print(appointments_df[["appointment_type", "no_show", "lead_time_days"]].head())

    print("\nGenerating synthetic billing records...")
    billing_df = generate_billing_records(100)
    print(f"Generated {len(billing_df)} billing records")
    print(billing_df[["bill_amount", "num_services", "is_fraud"]].head())

    print("\nGenerating synthetic admission records...")
    admissions_df = generate_admission_records(100)
    print(f"Generated {len(admissions_df)} admission records")
    print(admissions_df[["diagnosis", "readmission_risk_score", "readmission_within_30_days"]].head())

    print("\nGenerating synthetic drug pairs...")
    drugs_df = generate_drug_pairs(100)
    print(f"Generated {len(drugs_df)} drug pairs")
    print(drugs_df[["drug1", "drug2", "severity", "interacts"]].head())

    print("\nGenerating time series occupancy data...")
    occupancy_df = generate_time_series_occupancy(90)
    print(f"Generated {len(occupancy_df)} occupancy records")
    print(occupancy_df[occupancy_df["ward_type"] == "ICU"].head())
