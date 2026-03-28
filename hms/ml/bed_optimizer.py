"""
Bed & Resource Demand Forecaster using LSTM and ARIMA.
Predicts bed occupancy and resource needs for hospital wards.
"""

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Tuple, Any, Optional
import sys
sys.path.append("/Users/debanjansahoo5/Desktop/debanjanMad1/MAD1 Proj/hms")

from config import BED_OPTIMIZER_MODEL, BED_OPTIMIZER_CONFIG

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False


class BedOptimizer:
    """
    LSTM-based bed demand forecaster with ARIMA fallback.
    """

    def __init__(self):
        """Initialize bed optimizer."""
        self.lstm_model = None
        self.arima_model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        self.historical_mean = None
        self.historical_std = None

    def preprocess(self, raw_input: dict) -> Dict[str, Any]:
        """
        Preprocess occupancy data.

        Args:
            raw_input: Dictionary with occupancy history

        Returns:
            Processed data dictionary
        """
        ward_type = raw_input.get("ward_type", "general")
        historical_occupancy = raw_input.get("historical_occupancy", [])
        forecast_days = raw_input.get("forecast_days", 7)

        if isinstance(historical_occupancy, list):
            occupancy_array = np.array(historical_occupancy).reshape(-1, 1)
        else:
            occupancy_array = historical_occupancy

        return {
            "ward_type": ward_type,
            "occupancy_array": occupancy_array,
            "forecast_days": forecast_days,
        }

    def _create_sequences(self, data: np.ndarray, lookback: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training."""
        X, y = [], []
        for i in range(lookback, len(data)):
            X.append(data[i - lookback:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def train(self, df: pd.DataFrame) -> None:
        """
        Train the bed optimizer on historical occupancy data.

        Args:
            df: DataFrame with occupancy time series
        """
        print("Training Bed Optimizer...")

        # Get occupancy data grouped by ward
        for ward_type in df["ward_type"].unique():
            ward_data = df[df["ward_type"] == ward_type].sort_values("date")
            occupancy = ward_data["occupancy"].values.reshape(-1, 1)

            # Store statistics
            self.historical_mean = occupancy.mean()
            self.historical_std = occupancy.std()

            # Scale data
            scaled_occupancy = self.scaler.fit_transform(occupancy)

            if KERAS_AVAILABLE and len(scaled_occupancy) > 60:
                # Train LSTM if Keras available
                self._train_lstm(scaled_occupancy)
                self.is_trained = True
            else:
                # Fallback to simple statistics
                print("Using statistical forecasting (LSTM/Keras not available)")
                self.is_trained = True

    def _train_lstm(self, scaled_data: np.ndarray) -> None:
        """Train LSTM model."""
        X, y = self._create_sequences(scaled_data, lookback=30)

        if len(X) < 10:
            print("Not enough data for LSTM training")
            return

        # Reshape for LSTM
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Build LSTM model
        self.lstm_model = Sequential([
            LSTM(BED_OPTIMIZER_CONFIG["lstm_units"], activation="relu",
                 input_shape=(X.shape[1], 1)),
            Dropout(BED_OPTIMIZER_CONFIG["lstm_dropout"]),
            LSTM(BED_OPTIMIZER_CONFIG["lstm_units"], activation="relu"),
            Dropout(BED_OPTIMIZER_CONFIG["lstm_dropout"]),
            Dense(1)
        ])

        self.lstm_model.compile(optimizer=Adam(), loss="mse")

        # Train
        self.lstm_model.fit(
            X, y,
            epochs=BED_OPTIMIZER_CONFIG["lstm_epochs"],
            batch_size=BED_OPTIMIZER_CONFIG["lstm_batch_size"],
            verbose=0
        )
        print("LSTM model trained successfully")

    def predict(self, raw_input: dict) -> dict:
        """
        Forecast bed demand.

        Args:
            raw_input: Dictionary with occupancy history

        Returns:
            Dictionary with forecast and recommendations
        """
        processed = self.preprocess(raw_input)
        ward_type = processed["ward_type"]
        occupancy_array = processed["occupancy_array"]
        forecast_days = processed["forecast_days"]

        if not self.is_trained:
            return {
                "error": "Model not trained",
                "ward": ward_type,
                "forecast": [],
                "peak_day": None,
                "overflow_risk": False,
                "recommended_action": "Train model first"
            }

        # Scale occupancy
        scaled_occupancy = self.scaler.fit_transform(occupancy_array)

        # Generate forecast
        if self.lstm_model is not None:
            forecast = self._forecast_lstm(scaled_occupancy, forecast_days)
        else:
            forecast = self._forecast_statistical(occupancy_array, forecast_days)

        # Inverse transform to get actual occupancy
        forecast_unscaled = self.scaler.inverse_transform(forecast.reshape(-1, 1)).flatten()

        # Generate forecast with dates
        from datetime import datetime, timedelta
        start_date = datetime.now()
        forecast_data = []
        peak_occupancy = 0
        peak_day = None

        for i, occupancy in enumerate(forecast_unscaled):
            date = start_date + timedelta(days=i)
            # Simple confidence interval (±15%)
            ci_lower = max(0, occupancy * 0.85)
            ci_upper = occupancy * 1.15

            forecast_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_beds_needed": int(occupancy),
                "confidence_interval": [int(ci_lower), int(ci_upper)]
            })

            if occupancy > peak_occupancy:
                peak_occupancy = occupancy
                peak_day = date.strftime("%Y-%m-%d")

        # Determine overflow risk and capacity based on ward type
        ward_capacities = {"general": 100, "ICU": 25, "private": 50, "maternity": 40}
        ward_capacity = ward_capacities.get(ward_type, 100)

        overflow_risk = peak_occupancy > (ward_capacity * 0.9)

        if overflow_risk:
            additional_beds = int(peak_occupancy - (ward_capacity * 0.9))
            recommended_action = f"Pre-arrange {additional_beds} additional {ward_type} beds by {peak_day}"
        else:
            recommended_action = "No immediate action required. Standard monitoring continues."

        return {
            "ward": ward_type,
            "forecast": forecast_data,
            "peak_day": peak_day,
            "peak_occupancy": int(peak_occupancy),
            "ward_capacity": ward_capacity,
            "overflow_risk": overflow_risk,
            "recommended_action": recommended_action
        }

    def _forecast_lstm(self, scaled_data: np.ndarray, days: int) -> np.ndarray:
        """Generate LSTM forecast."""
        lookback = 30
        forecast = []
        current_seq = scaled_data[-lookback:].flatten()

        for _ in range(days):
            current_seq_reshaped = current_seq.reshape(1, lookback, 1)
            next_pred = self.lstm_model.predict(current_seq_reshaped, verbose=0)[0, 0]
            forecast.append(next_pred)
            current_seq = np.append(current_seq[1:], next_pred)

        return np.array(forecast)

    def _forecast_statistical(self, data: np.ndarray, days: int) -> np.ndarray:
        """Generate simple statistical forecast."""
        mean = data.mean()
        std = data.std()
        # Simple random walk with drift
        forecast = []
        last_value = data[-1, 0]

        for _ in range(days):
            noise = np.random.normal(0, std * 0.1)
            next_value = last_value + noise
            forecast.append(max(0, next_value))
            last_value = next_value

        return np.array(forecast)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate forecasting model.

        Args:
            X_test: Test input sequences
            y_test: Test target values

        Returns:
            Dictionary with evaluation metrics
        """
        if self.lstm_model is None:
            return {"error": "Model not trained"}

        from sklearn.metrics import mean_absolute_error, mean_squared_error

        y_pred = self.lstm_model.predict(X_test, verbose=0)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
        }

    def save_model(self, path: str = None) -> None:
        """Save model to disk."""
        if path is None:
            path = str(BED_OPTIMIZER_MODEL)

        model_data = {
            "lstm_model": self.lstm_model,
            "scaler": self.scaler,
            "historical_mean": self.historical_mean,
            "historical_std": self.historical_std,
        }
        joblib.dump(model_data, path)
        print(f"Bed optimizer saved to {path}")

    def load_model(self, path: str = None) -> None:
        """Load model from disk."""
        if path is None:
            path = str(BED_OPTIMIZER_MODEL)

        model_data = joblib.load(path)
        self.lstm_model = model_data["lstm_model"]
        self.scaler = model_data["scaler"]
        self.historical_mean = model_data["historical_mean"]
        self.historical_std = model_data["historical_std"]
        self.is_trained = True
        print(f"Bed optimizer loaded from {path}")


if __name__ == "__main__":
    """Demo: Test bed optimizer"""
    from utils.synthetic_data import generate_time_series_occupancy

    print("Generating synthetic occupancy data...")
    occupancy_df = generate_time_series_occupancy(365)

    # Train on ICU data
    icu_data = occupancy_df[occupancy_df["ward_type"] == "ICU"]

    optimizer = BedOptimizer()
    optimizer.train(occupancy_df)

    # Test forecast
    test_input = {
        "ward_type": "ICU",
        "historical_occupancy": icu_data["occupancy"].tail(90).values.tolist(),
        "forecast_days": 7
    }

    print("\nGenerating forecast...")
    result = optimizer.predict(test_input)
    print("\nBed Demand Forecast:")
    print(f"Ward: {result['ward']}")
    print(f"Peak Day: {result['peak_day']}")
    print(f"Overflow Risk: {result['overflow_risk']}")
    print(f"Recommended Action: {result['recommended_action']}")
    print(f"\nForecast (first 3 days):")
    for forecast_day in result["forecast"][:3]:
        print(f"  {forecast_day['date']}: {forecast_day['predicted_beds_needed']} beds (CI: {forecast_day['confidence_interval']})")

    print("\nSaving model...")
    optimizer.save_model()
