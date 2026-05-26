# TSLA Stock Price Prediction & Real-Time Visualization Dashboard

A real-time stock monitoring and predictive analytics dashboard specifically optimized for TSLA. This project features a high-performance **FastAPI** backend with automated data collection and **LSTM model training**, paired with a beautiful **Next.js** frontend with live interactive charts (using Lightweight Charts).

## Features

- **Real-Time Data Streaming:** Real-time TSLA stock price updates via WebSockets connected to Finnhub.
- **LSTM Machine Learning Engine:** Multi-step time-series prediction trained on historical TSLA daily data.
- **Green Area & Candlestick Predictions:** Directly overlay 15-day forward-looking predictions onto candlestick or area charts in green.
- **Historical Analysis:** Support for daily/hourly intervals with interactive zooming, panning, and volume indicators.
- **Modern Premium Dashboard:** Designed with sleek HSL-tailored colors, dark-mode styling, glassmorphism UI, and smooth hover effects.

---

## Directory Structure

```
stockprice prediction/
├── backend/            # FastAPI Backend & ML Scripts
│   ├── app/            # FastAPI Application Source
│   ├── scripts/        # Data Collector & Model Training Scripts
│   ├── saved_models/   # Trained Model Artifacts (LSTM weights, Scalers)
│   ├── requirements.txt
│   └── .env.example
├── frontend/           # Next.js Frontend App
│   ├── app/            # Next.js App Router Pages
│   ├── components/     # UI Components (Charts, Stats cards)
│   ├── package.json
│   └── .env.example
└── README.md           # Project Documentation
```

---

## Getting Started

### 1. Backend Setup (FastAPI & ML)

Navigate to the `backend` directory:
```bash
cd backend
```

Create a virtual environment and activate it:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Set up your environment variables:
Create a `.env` file based on `.env.example`:
```env
FINNHUB_API_KEY=your_finnhub_api_key_here
```

#### Fetch Historical TSLA Data
Before training the LSTM model, download historical TSLA data using the collector script:
```bash
python scripts/data_collector.py
```

#### Train the LSTM Model
Train the LSTM model for TSLA 1-day timeframe predictions:
```bash
python scripts/train_lstm.py
```
This saves the trained PyTorch model and scaler artifacts under the `saved_models` directory.

#### Start the Backend Server
Run the FastAPI development server:
```bash
python -m uvicorn main:app --reload --port 8000
```
The backend API is served at `http://localhost:8000`.

---

### 2. Frontend Setup (Next.js)

Navigate to the `frontend` directory:
```bash
cd ../frontend
```

Install the dependencies:
```bash
npm install
```

Set up your environment variables:
Create a `.env.local` file based on `.env.example`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/stocks
```

Start the Next.js development server:
```bash
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Technology Stack

- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, Lightweight Charts (Financial Charting Library).
- **Backend:** FastAPI, Python, WebSockets, PyTorch, Scikit-Learn, Pandas, yfinance/Finnhub APIs.
