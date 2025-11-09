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
import os
import requests as re
import logging

# Configure GPU usage
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use GPU ID 0 (strongest one)
import tensorflow as tf

# Suppress specific TensorFlow warnings that are not actionable
tf.get_logger().setLevel("ERROR")

# Also suppress the specific autotuning warning
logging.getLogger("tensorflow").setLevel(logging.ERROR)

# Configure TensorFlow to use GPU memory growth
gpus = tf.config.experimental.list_physical_devices("GPU")
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(
            f"Using GPU: {tf.config.experimental.get_device_details(gpus[0])}"
        )
    except RuntimeError as e:
        print(f"GPU configuration error: {e}")

# API Configuration
API_BASE_URL = "https://esp.savietto.app"


def login(user, password):
    """Login to the API and get an access token"""
    headers = {"Content-Type": "application/json"}
    data = {"username": user, "password": password}

    response = re.post(
        f"{API_BASE_URL}/auth/login", json=data, headers=headers
    )
    if response.status_code == 200:
        return response.json()
    print(response.text)
    return None

USERNAME = "superadmin"
PASSWORD = "supersecret"

ACCESS_TOKEN = None

# Model parameters
SEQUENCE_LENGTH = 288 * 2  # last 2 days
TRAIN_TEST_SPLIT = 0.8
EPOCHS = 100
BATCH_SIZE = 32
MIN_INTERVAL_MINUTES = (
    5  # Configurable parameter for minimum interval between readings
)
PAGE_SIZE = 100


def load_data_from_csv():
    """Load measurements from CSV if available"""
    csv_file = "measurements.csv"
    if os.path.exists(csv_file):
        print("Loading data from CSV...")
        df = pd.read_csv(csv_file)
        # Convert timestamp column to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df.to_dict("records")
    return None


async def fetch_measurements(session, page=1):
    """Fetch measurements from the API with pagination"""
    global ACCESS_TOKEN
    if not ACCESS_TOKEN:
        tokens = login(USERNAME, PASSWORD)
        ACCESS_TOKEN = tokens["access_token"]        
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    async with session.get(
        f"{API_BASE_URL}/measurements/?page={page}&page_size={PAGE_SIZE}&min_interval_minutes={MIN_INTERVAL_MINUTES}",
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
                activation="tanh",
                input_shape=(sequence_length, n_features),
                return_sequences=True,
                dropout=0.2,
                recurrent_dropout=0.2,
            ),
            LSTM(32, activation="tanh", return_sequences=False, dropout=0.2, recurrent_dropout=0.2),
            RepeatVector(sequence_length),
            LSTM(32, activation="tanh", return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
            LSTM(64, activation="tanh", return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
            TimeDistributed(Dense(n_features)),
        ]
    )

    # Use Adam with gradient clipping to prevent exploding gradients
    optimizer = Adam(learning_rate=0.001, clipnorm=1.0)
    model.compile(optimizer=optimizer, loss="mse")
    return model


async def main():
    """Main training function"""
    print("Starting anomaly detection model training...")

    # Check if we have cached CSV data first
    csv_data = load_data_from_csv()
    if csv_data is not None:
        print("Using cached data from CSV...")
        measurements = csv_data
    else:
        # 1. Fetch data from API
        print("Fetching measurements from API...")
        measurements = await fetch_all_measurements()

        # Save to CSV for future use
        if measurements:
            df = pd.DataFrame(measurements)
            df.to_csv("measurements.csv", index=False)
            print("Data saved to measurements.csv")

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

    # Calculate additional quality metrics
    mean_mse = np.mean(mse)
    std_mse = np.std(mse)
    max_mse = np.max(mse)
    min_mse = np.min(mse)

    print("Reconstruction error statistics:")
    print(f"  Mean MSE: {mean_mse:.8f}")
    print(f"  Std MSE: {std_mse:.8f}")
    print(f"  Min MSE: {min_mse:.8f}")
    print(f"  Max MSE: {max_mse:.8f}")
    print(f"Reconstruction error threshold (95th percentile): {threshold}")

    # Analyze model performance
    anomalies = mse > threshold
    num_anomalies = np.sum(anomalies)
    anomaly_rate = num_anomalies / len(mse) * 100

    print("\nModel Quality Assessment:")
    print(f"  Total test samples: {len(mse)}")
    print(f"  Detected anomalies: {num_anomalies}")
    print(f"  Anomaly rate: {anomaly_rate:.2f}%")

    # 5. Save model and scaler
    model.save("anomaly_detector_model.keras")
    with open("scaler.json", "w") as f:
        json.dump(scaler.data_range_.tolist(), f)
        json.dump(scaler.data_min_.tolist(), f)

    print("Model training completed and saved!")


if __name__ == "__main__":
    asyncio.run(main())
