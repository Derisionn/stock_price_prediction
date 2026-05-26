import yfinance as yf
import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DataCollector")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def download_data(symbol: str = "TSLA", interval: str = "1d", period: str = "10y"):
    """
    Downloads historical data from yfinance and saves it to a CSV file.
    For minute data (1m), yfinance only allows max 7 days.
    For daily data (1d), yfinance allows max 10 years or more.
    """
    logger.info(f"Downloading {period} of {interval} data for {symbol}...")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        logger.error(f"No data found for {symbol}. Try a different interval/period.")
        return

    # Clean up dataframe
    df = df.reset_index()
    # yfinance uses 'Date' or 'Datetime' depending on the interval
    time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
    
    # Standardize column names
    df = df.rename(columns={
        time_col: "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    # We only need these columns
    df = df[["time", "open", "high", "low", "close", "volume"]]
    
    # Convert time to unix timestamp
    df["time"] = pd.to_datetime(df["time"]).astype(int) // 10**9

    csv_path = os.path.join(DATA_DIR, f"{symbol}_{interval}.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved {len(df)} rows to {csv_path}")

if __name__ == "__main__":
    # We download 5 years of daily data for TSLA
    download_data("TSLA", interval="1d", period="5y")
    # For intra-day simulation, we could also fetch 60 days of 1h data
    download_data("TSLA", interval="1h", period="730d") # yfinance max for 1h is 730d
