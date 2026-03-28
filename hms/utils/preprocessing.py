"""
Data preprocessing utilities for HMS AI/ML System.
Handles feature engineering, scaling, and data transformation.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import Tuple, Dict, List, Union


def scale_features(X: pd.DataFrame, scaler_type: str = "standard") -> Tuple[pd.DataFrame, Union[StandardScaler, MinMaxScaler]]:
    """
    Scale numerical features.

    Args:
        X: Input features
        scaler_type: 'standard' or 'minmax'

    Returns:
        Scaled DataFrame and fitted scaler
    """
    if scaler_type == "standard":
        scaler = StandardScaler()
    else:
        scaler = MinMaxScaler()

    X_scaled = scaler.fit_transform(X)
    return pd.DataFrame(X_scaled, columns=X.columns), scaler


def encode_categorical(X: pd.DataFrame, categorical_cols: List[str]) -> Tuple[pd.DataFrame, Dict[str, LabelEncoder]]:
    """
    Encode categorical features using LabelEncoder.

    Args:
        X: Input features
        categorical_cols: List of categorical column names

    Returns:
        DataFrame with encoded categories and encoders dictionary
    """
    X_copy = X.copy()
    encoders = {}

    for col in categorical_cols:
        if col in X_copy.columns:
            encoder = LabelEncoder()
            X_copy[col] = encoder.fit_transform(X_copy[col].astype(str))
            encoders[col] = encoder

    return X_copy, encoders


def extract_symptom_features(symptoms_series: pd.Series, max_features: int = 100) -> pd.DataFrame:
    """
    Convert symptom text to TF-IDF features.

    Args:
        symptoms_series: Series of symptom strings (semicolon-separated)
        max_features: Maximum number of TF-IDF features

    Returns:
        DataFrame with TF-IDF features
    """
    # Handle missing values
    symptoms_text = symptoms_series.fillna("none").astype(str)

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        lowercase=True,
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(symptoms_text)
    feature_names = vectorizer.get_feature_names_out()

    return pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names), vectorizer


def one_hot_encode(X: pd.DataFrame, categorical_cols: List[str]) -> pd.DataFrame:
    """
    Apply one-hot encoding to categorical features.

    Args:
        X: Input features
        categorical_cols: List of categorical column names

    Returns:
        DataFrame with one-hot encoded features
    """
    return pd.get_dummies(X, columns=categorical_cols, drop_first=True)


def handle_missing_values(X: pd.DataFrame, strategy: str = "mean") -> pd.DataFrame:
    """
    Handle missing values in dataframe.

    Args:
        X: Input DataFrame
        strategy: 'mean', 'median', 'forward_fill', 'drop'

    Returns:
        DataFrame with missing values handled
    """
    X_copy = X.copy()

    if strategy == "mean":
        X_copy = X_copy.fillna(X_copy.mean(numeric_only=True))
    elif strategy == "median":
        X_copy = X_copy.fillna(X_copy.median(numeric_only=True))
    elif strategy == "forward_fill":
        X_copy = X_copy.fillna(method="ffill").fillna(method="bfill")
    elif strategy == "drop":
        X_copy = X_copy.dropna()

    return X_copy


def extract_comorbidity_features(comorbidity_series: pd.Series) -> pd.DataFrame:
    """
    Extract binary features from comorbidity strings.

    Args:
        comorbidity_series: Series of comorbidities (semicolon-separated)

    Returns:
        DataFrame with binary comorbidity features
    """
    all_comorbidities = set()

    for comorbidities_str in comorbidity_series:
        if isinstance(comorbidities_str, str) and comorbidities_str != "none":
            all_comorbidities.update(comorbidities_str.split(";"))

    features = {}
    for comorbidity in sorted(all_comorbidities):
        features[f"has_{comorbidity.lower().replace(' ', '_')}"] = [
            1 if isinstance(c_str, str) and comorbidity in c_str else 0
            for c_str in comorbidity_series
        ]

    return pd.DataFrame(features)


def normalize_vital_signs(X: pd.DataFrame, vital_signs_config: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
    """
    Normalize vital signs to 0-1 range based on medical valid ranges.

    Args:
        X: Input DataFrame with vital signs
        vital_signs_config: Dict mapping column name to (min, max) valid range

    Returns:
        DataFrame with normalized vital signs
    """
    X_normalized = X.copy()

    for column, (min_val, max_val) in vital_signs_config.items():
        if column in X_normalized.columns:
            # Clip values to valid range, then normalize
            X_normalized[column] = (X_normalized[column] - min_val) / (max_val - min_val)
            X_normalized[column] = X_normalized[column].clip(0, 1)

    return X_normalized


def create_age_bins(age_series: pd.Series, bins: List[int] = None) -> pd.Series:
    """
    Bin age into categories.

    Args:
        age_series: Series of ages
        bins: List of bin edges

    Returns:
        Series with binned age categories
    """
    if bins is None:
        bins = [0, 18, 30, 45, 60, 75, 120]

    labels = ["0-18", "18-30", "30-45", "45-60", "60-75", "75+"]

    return pd.cut(age_series, bins=bins, labels=labels, right=False)


def create_time_features(date_series: pd.Series) -> pd.DataFrame:
    """
    Extract temporal features from date column.

    Args:
        date_series: Series of dates

    Returns:
        DataFrame with temporal features
    """
    date_series = pd.to_datetime(date_series)

    return pd.DataFrame({
        "year": date_series.dt.year,
        "month": date_series.dt.month,
        "day": date_series.dt.day,
        "day_of_week": date_series.dt.dayofweek,
        "week_of_year": date_series.dt.isocalendar().week,
        "quarter": date_series.dt.quarter,
        "is_weekend": (date_series.dt.dayofweek >= 5).astype(int),
    })


def standardize_text(text_series: pd.Series) -> pd.Series:
    """
    Standardize text (lowercase, strip whitespace).

    Args:
        text_series: Series of text strings

    Returns:
        Standardized text series
    """
    return text_series.str.lower().str.strip()


def create_interaction_features(X: pd.DataFrame, features: List[Tuple[str, str]]) -> pd.DataFrame:
    """
    Create interaction features between pairs of columns.

    Args:
        X: Input DataFrame
        features: List of tuples (col1, col2) to create interactions

    Returns:
        DataFrame with added interaction features
    """
    X_interaction = X.copy()

    for col1, col2 in features:
        if col1 in X.columns and col2 in X.columns:
            interaction_name = f"{col1}_x_{col2}"
            X_interaction[interaction_name] = X[col1] * X[col2]

    return X_interaction


def create_polynomial_features(X: pd.DataFrame, columns: List[str], degree: int = 2) -> pd.DataFrame:
    """
    Create polynomial features.

    Args:
        X: Input DataFrame
        columns: Columns to create polynomial features for
        degree: Polynomial degree

    Returns:
        DataFrame with polynomial features
    """
    X_poly = X.copy()

    for col in columns:
        if col in X.columns:
            for d in range(2, degree + 1):
                X_poly[f"{col}_^{d}"] = X[col] ** d

    return X_poly


if __name__ == "__main__":
    """Demo: Test preprocessing functions"""
    print("Testing preprocessing utilities...")

    # Create sample data
    df = pd.DataFrame({
        "age": [25, 45, 60, 35, 55],
        "gender": ["M", "F", "M", "F", "M"],
        "temperature": [37.0, 38.5, 36.8, 37.2, 39.0],
        "heart_rate": [72, 85, 68, 75, 90],
        "symptoms": ["fever;cough", "fever", "none", "cough;fatigue", "fever;chest_pain"],
        "comorbidities": ["none", "Hypertension", "Diabetes", "none", "Hypertension;Diabetes"],
    })

    print("\nOriginal data:")
    print(df)

    print("\nScaled numerical features:")
    scaled_df, scaler = scale_features(df[["age", "temperature", "heart_rate"]])
    print(scaled_df)

    print("\nCategorical encoding:")
    encoded_df, encoders = encode_categorical(df, ["gender"])
    print(encoded_df[["gender"]].head())

    print("\nSymptom TF-IDF features:")
    symptom_features, vectorizer = extract_symptom_features(df["symptoms"], max_features=5)
    print(symptom_features.head())

    print("\nComorbidity features:")
    comorbidity_features = extract_comorbidity_features(df["comorbidities"])
    print(comorbidity_features.head())

    print("\nAge bins:")
    age_binned = create_age_bins(df["age"])
    print(age_binned)
