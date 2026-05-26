import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from app.ml.model import LSTMModel
from scripts.dataset import prepare_data, StockDataset, MODELS_DIR

def train(symbol="TSLA", interval="1d", epochs=100, batch_size=64):
    print(f"Preparing data for {symbol} {interval}...")
    X_train, y_train, X_test, y_test, scaler = prepare_data(symbol, interval, seq_length=60, is_training=True)
    
    train_dataset = StockDataset(X_train, y_train)
    test_dataset = StockDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    model = LSTMModel(input_size=7, hidden_size=64, num_layers=2, output_size=4)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    train_losses = []
    test_losses = []
    best_loss = float('inf')
    
    model_path = os.path.join(MODELS_DIR, f"{symbol}_{interval}_model.pt")

    print(f"Starting training for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        epoch_train_loss = 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            epoch_train_loss += loss.item()
            
        epoch_train_loss /= len(train_loader)
        train_losses.append(epoch_train_loss)
        
        # Evaluation
        model.eval()
        epoch_test_loss = 0
        with torch.no_grad():
            for X_batch, y_batch in test_loader:
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch)
                epoch_test_loss += loss.item()
                
        epoch_test_loss /= len(test_loader)
        test_losses.append(epoch_test_loss)
        
        if epoch_test_loss < best_loss:
            best_loss = epoch_test_loss
            torch.save(model.state_dict(), model_path)
            
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}] | Train Loss: {epoch_train_loss:.6f} | Test Loss: {epoch_test_loss:.6f}")

    print(f"Training complete! Best Test Loss: {best_loss:.6f}")
    print(f"Best model saved to {model_path}")
    
    # Plotting metrics
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label="Train Loss")
    plt.plot(test_losses, label="Test Loss")
    plt.title(f"LSTM Training Metrics for {symbol}")
    plt.xlabel("Epochs")
    plt.ylabel("MSE Loss")
    plt.legend()
    plt.grid(True)
    
    plot_path = os.path.join(MODELS_DIR, f"{symbol}_{interval}_loss_curve.png")
    plt.savefig(plot_path)
    print(f"Loss curve saved to {plot_path}")

if __name__ == "__main__":
    train(symbol="TSLA", interval="1d", epochs=50)
