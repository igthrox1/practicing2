import asyncio, websockets, json

URL = "wss://fstream.binance.com/ws/{}@markPrice"

async def fetch_binance(btcusdt):
    while True:
        try:
            async with websockets.connect(URL.format(btcusdt.lower())) as ws:
                print("✅ Binance WS connected")
                while True:
                    msg = json.loads(await ws.recv())
                    funding_rate = float(msg.get("r", 0))
                    next_settlement = int(msg.get("T", 0)) / 1000
                    mark_price= float(msg["p"])
                    print(f"Binance | Funding Rate: {funding_rate} | Next Settlement: {next_settlement} | Mark Price: {mark_price}")
        except Exception as e:
            print("Binance WS error:", e)
            await asyncio.sleep(2)
asyncio.run(fetch_binance('btcusdt'))
