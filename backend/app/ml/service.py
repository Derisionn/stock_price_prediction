import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing import List, Dict
import logging
import time

from app.ml.model import LSTMModel

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'saved_models')
        self.models = {}
        self.scalers = {}

    def _load_model(self, symbol: str, interval: str):
        cache_key = f"{symbol}_{interval}"
        if cache_key in self.models:
            return self.models[cache_key], self.scalers[cache_key]

        model_path = os.path.join(self.models_dir, f"{symbol}_{interval}_model.pt")
        scaler_path = os.path.join(self.models_dir, f"{symbol}_{interval}_scaler.pkl")

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise ValueError(f"Offline model for {cache_key} not found. Please train it first.")

        # Input size 7 (open, high, low, close, volume, rsi, sma_20)
        model = LSTMModel(input_size=7, hidden_size=64, num_layers=2, output_size=4)
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        model.eval()

        import joblib
        scaler = joblib.load(scaler_path)

        self.models[cache_key] = model
        self.scalers[cache_key] = scaler
        return model, scaler

    def predict(self, symbol: str, interval: str, candles: List[Dict], steps: int = 15, seq_length: int = 60) -> List[Dict]:
        import ta
        if len(candles) <= seq_length + 20: # need extra for 20-period SMA
            raise ValueError(f"Need at least {seq_length + 20} candles for prediction and indicators.")
            
        # Add Technical Indicators
        df = pd.DataFrame(candles)
        df = df.sort_values("time")
        df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
        df["sma_20"] = ta.trend.SMAIndicator(close=df["close"], window=20).sma_indicator()
        
        # Drop initial NaNs from MAs
        df = df.dropna()
        
        # Take the last `seq_length` rows
        df = df.tail(seq_length)
        features = ["open", "high", "low", "close", "volume", "rsi", "sma_20"]
        data = df[features].values

        model, scaler = self._load_model(symbol, interval)
        
        data_scaled = scaler.transform(data)
        
        current_seq = torch.FloatTensor(data_scaled).unsqueeze(0)
        
        predictions = []
        last_time = df.iloc[-1]['time']
        
        interval_sec = 60
        if len(candles) >= 2:
            interval_sec = candles[-1]['time'] - candles[-2]['time']
            
        with torch.no_grad():
            for _ in range(steps):
                pred = model(current_seq)
                pred_numpy = pred.numpy()
                predictions.append(pred_numpy[0])
                
                # To feed the prediction back, we need to invent values for volume, rsi, sma_20.
                # For simplicity in this autoregressive loop, we keep them constant (last known value).
                last_features = current_seq[0, -1, 4:].clone()
                full_pred = torch.cat([pred[0], last_features])
                
                current_seq = torch.cat((current_seq[:, 1:, :], full_pred.unsqueeze(0).unsqueeze(0)), dim=1)
                
        # To inverse transform, we only care about the first 4 columns, but scaler expects 7
        # Pad with zeros
        padded_predictions = np.zeros((steps, 7))
        padded_predictions[:, :4] = np.array(predictions)
        
        predictions_inverse = scaler.inverse_transform(padded_predictions)
        
        # Calculate average real volatility from the last 10 candles to make predictions look realistic
        recent_candles = candles[-10:] if len(candles) >= 10 else candles
        avg_body = np.mean([abs(c['open'] - c['close']) for c in recent_candles])
        avg_wick = np.mean([c['high'] - c['low'] for c in recent_candles])

        results = []
        for i in range(steps):
            pred_time = last_time + (i + 1) * interval_sec
            
            p_open = float(predictions_inverse[i][0])
            p_high = float(predictions_inverse[i][1])
            p_low = float(predictions_inverse[i][2])
            p_close = float(predictions_inverse[i][3])
            
            # Use the model's general trend (center point), but force realistic candle sizes
            center = (p_open + p_close) / 2
            is_green = p_close > p_open
            
            p_open = (center - avg_body / 2) if is_green else (center + avg_body / 2)
            p_close = (center + avg_body / 2) if is_green else (center - avg_body / 2)
            
            real_high = max(p_open, p_close) + max(0, (avg_wick - avg_body) / 2)
            real_low = min(p_open, p_close) - max(0, (avg_wick - avg_body) / 2)
            
            results.append({
                "time": int(pred_time),
                "open": p_open,
                "high": real_high,
                "low": real_low,
                "close": p_close,
                "isPrediction": True
            })
            
        return results

ml_service = MLService()
