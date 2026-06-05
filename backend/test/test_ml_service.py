import asyncio
import httpx
from datetime import datetime, timedelta

ML_SERVICE_URL = "http://localhost:8000"

async def test_ml_prediction_endpoint():
    """
    Tests the ML prediction endpoint by sending 200 mock candles 
    and printing the response.
    """
    print(f"Testing ML Service at {ML_SERVICE_URL}/predict...")
    
    # Generate 300 mock 1-minute candles
    mock_candles = []
    base_time = datetime.utcnow().replace(second=0, microsecond=0) - timedelta(minutes=300)
    
    for i in range(300):
        candle_time = base_time + timedelta(minutes=i)
        mock_candles.append({
            "timestamp": candle_time.isoformat() + "Z",
            "open": 100.0 + i * 0.1,
            "high": 105.0 + i * 0.1,
            "low": 95.0 + i * 0.1,
            "close": 102.0 + i * 0.1,
            "volume": 1000.0
        })
        
    payload = {"candles": mock_candles}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{ML_SERVICE_URL}/predict", json=payload, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success! Received response from ML service.")
                print(f"Status: {data.get('status')}")
                
                predictions = data.get("predictions", [])
                print(f"Received {len(predictions)} predicted candles:")
                
                for i, p in enumerate(predictions[:3]): # print first 3
                    print(f"  {i+1}. {p['timestamp']} -> Close: {p.get('Close')}")
                
                print("  ... (showing first 3 of 15)")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error connecting to ML service: {e}")

if __name__ == "__main__":
    asyncio.run(test_ml_prediction_endpoint())
