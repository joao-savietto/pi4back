"""
Training script for LSTM Autoencoder anomaly detection model
for temperature and humidity sensor data.
"""

import numpy as np
import pandas as pd
import asyncio
import aiohttp
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import json

# API Configuration
API_BASE_URL = "https://esp.savietto.app"
ACCESS_TOKEN = (
    "YOUR_ACCESS_TOKEN_HERE"  # Set this to your actual access token
)

# Model parameters
SEQUENCE_LENGTH = 50
TRAIN_TEST_SPLIT = 0.8
EPOCHS = 100
BATCH_SIZE = 32


async def fetch_measurements(session, page=1):
    """Fetch measurements from the API with pagination"""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    async with session.get(
        f"{API_BASE_URL}/api/measurements/?page={page}&page_size=100",
        headers=headers,
    ) as response:
        if response.status == 200:
            data = await response.json()
            return data["measurements"]
        else:
            print(f"Error fetching measurements: {response.status}")
            return []


async def fetch_all_measurements():
    """Fetch all measurements from the API"""
    async with aiohttp.ClientSession() as session:
        all_measurements = []
        page = 1

        while True:
            measurements = await fetch_measurements(session, page)
            if not measurements:
                break
            all_measurements.extend(measurements)
            print(f"Fetched {len(all_measurements)} measurements...")

            # Check if we've reached the end
            if len(measurements) < 100:  # Last page
                break

            page += 1

    return all_measurements


def preprocess_data(measurements):
    """Preprocess measurements data for training"""
    # Convert to DataFrame
    df = pd.DataFrame(measurements)

    # Convert timestamp to datetime if needed
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Sort by timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Extract temperature and humidity
    data = df[["temperature", "humidity"]].values

    return data


def create_sequences(data, sequence_length):
    """Create sequences for LSTM training"""
    X = []
    for i in range(len(data) - sequence_length):
        X.append(data[i : (i + sequence_length)])
    return np.array(X)


def build_lstm_autoencoder(sequence_length, n_features):
    """Build LSTM Autoencoder model"""
    # Encoder
    model = Sequential(
        [
            LSTM(
                64,
                activation="relu",
                input_shape=(sequence_length, n_features),
                return_sequences=True,
            ),
            LSTM(32, activation="relu", return_sequences=False),
            RepeatVector(sequence_length),
            LSTM(32, activation="relu", return_sequences=True),
            LSTM(64, activation="relu", return_sequences=True),
            TimeDistributed(Dense(n_features)),
        ]
    )

    model.compile(optimizer=Adam(learning_rate=0.001), loss="mse")
    return model


async def main():
    """Main training function"""
    print("Starting anomaly detection model training...")

    # 1. Fetch data from API
    print("Fetching measurements from API...")
    measurements = await fetch_all_measurements()

    if not measurements:
        print("No measurements found!")
        return

    # 2. Preprocess data
    print("Preprocessing data...")
    data = preprocess_data(measurements)

    # Normalize the data
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    # Create sequences
    X = create_sequences(scaled_data, SEQUENCE_LENGTH)

    if len(X) == 0:
        print("Not enough data to create sequences!")
        return

    # Split into train/test sets
    split_idx = int(len(X) * TRAIN_TEST_SPLIT)
    X_train = X[:split_idx]
    X_test = X[split_idx:]

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")

    # 3. Build and train model
    print("Building LSTM Autoencoder...")
    model = build_lstm_autoencoder(SEQUENCE_LENGTH, scaled_data.shape[1])

    # Early stopping callback
    early_stopping = EarlyStopping(
        monitor="loss", patience=10, restore_best_weights=True
    )

    print("Training model...")
    model.fit(
        X_train,
        X_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_test, X_test),
        callbacks=[early_stopping],
        verbose=1,
    )

    # 4. Calculate reconstruction errors on test set to determine threshold
    print("Calculating reconstruction errors...")
    predictions = model.predict(X_test)
    mse = np.mean(np.power(X_test - predictions, 2), axis=(1, 2))
    threshold = np.percentile(mse, 95)  # Use 95th percentile as threshold

    print(f"Reconstruction error threshold: {threshold}")

    # 5. Save model and scaler
    model.save("anomaly_detector_model.h5")
    with open("scaler.json", "w") as f:
        json.dump(scaler.data_range_.tolist(), f)
        json.dump(scaler.data_min_.tolist(), f)

    print("Model training completed and saved!")


if __name__ == "__main__":
    asyncio.run(main())
