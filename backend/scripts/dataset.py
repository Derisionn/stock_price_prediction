import pandas as pd
import numpy as np
import os
import ta
import joblib
from sklearn.preprocessing import MinMaxScaler
import torch
from torch.utils.data import Dataset

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)

class StockDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def prepare_data(symbol="TSLA", interval="1d", seq_length=60, is_training=True):
    """
    Loads data, adds indicators, splits, scales and returns DataLoaders/Arrays.
    """
    csv_path = os.path.join(DATA_DIR, f"{symbol}_{interval}.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Data file {csv_path} not found.")

    df = pd.read_csv(csv_path)
    
    # Sort chronologically just in case
    df = df.sort_values("time")

    # Add Technical Indicators
    # RSI (14 period)
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
    # Simple Moving Average (20 period)
    df["sma_20"] = ta.trend.SMAIndicator(close=df["close"], window=20).sma_indicator()
    
    # Drop rows with NaN values (created by the rolling windows of indicators)
    df = df.dropna()

    # Features: open, high, low, close, volume, rsi, sma_20
    features = ["open", "high", "low", "close", "volume", "rsi", "sma_20"]
    data = df[features].values
    
    scaler_path = os.path.join(MODELS_DIR, f"{symbol}_{interval}_scaler.pkl")

    if is_training:
        # Split 80/20
        split_idx = int(len(data) * 0.8)
        train_data = data[:split_idx]
        test_data = data[split_idx:]

        # Fit Scaler ONLY on training data
        scaler = MinMaxScaler(feature_range=(0, 1))
        train_scaled = scaler.fit_transform(train_data)
        test_scaled = scaler.transform(test_data)

        # Save scaler for later inference
        joblib.dump(scaler, scaler_path)

        X_train, y_train = create_sequences(train_scaled, seq_length)
        X_test, y_test = create_sequences(test_scaled, seq_length)

        return X_train, y_train, X_test, y_test, scaler
    else:
        # For inference
        scaler = joblib.load(scaler_path)
        data_scaled = scaler.transform(data)
        return data_scaled, scaler

def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        # Target is the next candle's OHLC (indices 0,1,2,3)
        y.append(data[i+seq_length][:4])
    return np.array(X), np.array(y)
