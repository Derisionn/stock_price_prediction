import asyncio
import websockets
import json

async def test():
    uri = 'wss://ws.finnhub.io?token=d88ouj1r01qq43442bg0d88ouj1r01qq43442bgg'
    try:
        async with websockets.connect(uri) as ws:
            print('connected')
            await ws.send(json.dumps({'type':'subscribe', 'symbol': 'AAPL'}))
            print('subscribed')
            # Wait for 3 seconds to see if we get anything
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=3.0)
                print('received:', message)
            except asyncio.TimeoutError:
                print('timeout waiting for message')
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
