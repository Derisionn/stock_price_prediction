import asyncio
import websockets
import json

async def test():
    async with websockets.connect('wss://stream.binance.com:9443/ws') as ws:
        await ws.send(json.dumps({'method':'SUBSCRIBE','params':['btcusdt@aggTrade'],'id':1}))
        print("Sent subscribe")
        print(await ws.recv())
        print(await ws.recv())
        print(await ws.recv())

asyncio.run(test())
