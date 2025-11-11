from typing import Optional, Any, List
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import json
import os
from fastapi import HTTPException

# Import the Measurement model for database access
from pi4.models.measurements import Measurement


class AnomalyDetectionService:
    """Service class for anomaly detection functionality.
    
    Note: This service fetches measurements with 5-minute intervals to match
    the training data pattern used for the LSTM autoencoder model.
    """

    def __init__(self):
        self.model: Optional[Any] = None
        self.scaler: Optional[MinMaxScaler] = None
        self.threshold_value: Optional[float] = None

    def load_model(self) -> bool:
        """Load the trained anomaly detection model and related components"""
        try:
            # Load the Keras model
            model_path = "anomaly_detector_model.keras"
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file {model_path} not found")

            self.model = load_model(model_path)

            # Load the scaler
            scaler_path = "scaler.json"
            if not os.path.exists(scaler_path):
                raise FileNotFoundError(
                    f"Scaler file {scaler_path} not found"
                )

            with open(scaler_path, "r") as f:
                # Handle the malformed JSON format from training script - it's two concatenated arrays
                content = f.read().strip()
                # Split on the closing bracket of first array to separate data
                if "][" in content:
                    parts = content.split("][")
                    range_data_str = (
                        parts[0] + "]"
                    )  # First part plus closing bracket
                    min_data_str = (
                        "[" + parts[1]
                    )  # Opening bracket plus second part

                    scaler_data_range = np.array(json.loads(range_data_str))
                    scaler_data_min = np.array(json.loads(min_data_str))
                else:
                    data = json.load(f)
                    # The JSON stores both range and min values - we need to reconstruct
                    scaler_data_range = np.array(
                        data[0]
                    )  # First array is the range
                    scaler_data_min = np.array(
                        data[1]
                    )  # Second array is the min

            # Create MinMaxScaler with loaded parameters
            self.scaler = MinMaxScaler()
            self.scaler.data_range_ = scaler_data_range
            self.scaler.data_min_ = scaler_data_min
            self.scaler.scale_ = 1.0 / (
                scaler_data_range + 1e-8
            )  # Avoid division by zero
            self.scaler.min_ = -scaler_data_min * self.scaler.scale_

            # Load threshold value from the training output
            # We'll hardcode a reasonable default for now, but ideally this should be stored separately
            self.threshold_value = (
                0.0009264747565845443  # From previous training run
            )
            print("Model and scaler loaded")
            return True

        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def preprocess_single_measurement(
        self, temperature: float, humidity: float
    ):
        """Preprocess a single measurement for prediction"""
        if self.scaler is None:
            raise HTTPException(status_code=500, detail="Model not loaded")

        # Create data in the same format used during training
        data = np.array([[temperature, humidity]])

        # Scale the data using the trained scaler
        scaled_data = self.scaler.transform(data)

        return scaled_data

    async def _fetch_recent_measurements(self, count: int) -> List[tuple]:
        """Fetch recent measurements from database for sequence creation with 5-minute intervals"""
        try:
            # Fetch more measurements than needed to account for interval filtering
            # We fetch 3x more to ensure we have enough after filtering
            fetch_count = count * 3
            all_measurements = await Measurement.all().order_by("-timestamp").limit(
                fetch_count
            ).all()
            
            # Apply 5-minute interval filtering (same logic as in measurements route)
            # Process in reverse order (newest first) then reverse back
            if all_measurements:
                filtered_measurements = []
                last_timestamp = None

                # Process from newest to oldest for interval filtering
                for measurement in all_measurements:
                    # If this is the first measurement, or if it's at least
                    # 5 minutes (300 seconds) after the last one
                    if (
                        last_timestamp is None
                        or (measurement.timestamp - last_timestamp).total_seconds()
                        >= 300  # 5 minutes = 300 seconds
                    ):
                        filtered_measurements.append(measurement)
                        last_timestamp = measurement.timestamp

                # Reverse to get chronological order (oldest first)
                filtered_measurements.reverse()
                
                # Take the most recent measurements after filtering
                filtered_measurements = filtered_measurements[-count:] if len(filtered_measurements) > count else filtered_measurements
                
                # Convert to list of tuples (temperature, humidity)
                return [(m.temperature, m.humidity) for m in filtered_measurements]
            else:
                return []
        except Exception as e:
            print(f"Error fetching recent measurements: {e}")
            # Return empty list if there's an error
            return []

    def _create_sequence_with_history(
        self,
        temperature: float,
        humidity: float,
        historical_measurements: List[tuple],
    ) -> np.ndarray:
        """Create proper sequence with historical measurements for prediction"""
        # Create a complete sequence of 576 measurements (2 days worth)
        sequence_length = 288 * 2  # Same as used during training (2 days)
        n_features = 2  # temperature and humidity

        # Build the sequence data - we need exactly sequence_length measurements
        sequence_data = []
        
        # If we don't have enough historical data, pad with oldest ones
        if len(historical_measurements) < sequence_length - 1:
            # Not enough historical data yet - pad with repeated oldest measurements  
            # This is a simplified approach; in production you might want to handle this differently
            if historical_measurements:
                # Use the oldest measurement for padding
                oldest_temp, oldest_hum = historical_measurements[0]
                oldest_scaled = self.preprocess_single_measurement(oldest_temp, oldest_hum)[0]
                # Pad with oldest measurements
                padding_count = sequence_length - 1 - len(historical_measurements)
                sequence_data.extend([oldest_scaled] * padding_count)
                # Add all historical measurements
                for temp, hum in historical_measurements:
                    scaled = self.preprocess_single_measurement(temp, hum)[0]
                    sequence_data.append(scaled)
            else:
                # No historical data - use current measurement for all
                current_scaled = self.preprocess_single_measurement(temperature, humidity)[0]
                sequence_data = [current_scaled] * (sequence_length - 1)
        else:
            # Use the most recent measurements available (last sequence_length-1 measurements)
            for temp, hum in historical_measurements[-(sequence_length - 1):]:
                scaled = self.preprocess_single_measurement(temp, hum)[0]
                sequence_data.append(scaled)

        # Preprocess and append current measurement at the end
        current_scaled = self.preprocess_single_measurement(temperature, humidity)[0]
        sequence_data.append(current_scaled)

        # Ensure we have exactly sequence_length elements
        if len(sequence_data) != sequence_length:
            raise ValueError(f"Sequence length mismatch: expected {sequence_length}, got {len(sequence_data)}")

        # Convert to numpy array and reshape for model input [samples, time_steps, features]
        sequence = np.array(sequence_data, dtype=np.float32)
        sequence = sequence.reshape(1, sequence_length, n_features)

        return sequence

    async def predict_anomaly(self, temperature: float, humidity: float):
        """Predict if a measurement is anomalous"""
        try:
            # Fetch the required number of historical measurements from database
            # We need 575 previous measurements plus current one = 576 total
            sequence_length = 288 * 2  # Same as used during training (2 days)
            
            # Get exactly the amount needed for sequence creation 
            historical_measurements = await self._fetch_recent_measurements(sequence_length - 1)

            # Create sequence with proper historical context from database
            sequence = self._create_sequence_with_history(
                temperature, humidity, historical_measurements
            )

            # Make prediction (reconstruction)
            reconstruction = self.model.predict(sequence, verbose=0)

            # Calculate MSE
            mse = np.mean(np.power(sequence - reconstruction, 2))

            # Check if it's anomalous
            is_anomalous = bool(mse > self.threshold_value)

            return {
                "is_anomalous": is_anomalous,
                "reconstruction_error": float(mse),
                "threshold": float(self.threshold_value),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error during prediction: {str(e)}"
            )


# Global instance to be initialized at startup
anomaly_service = AnomalyDetectionService()
