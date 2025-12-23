import asyncio
import websockets
import json
import time

URL = "wss://fstream.binance.com/ws/btcusdt@trade"

async def main():
    async with websockets.connect(URL) as ws:
        print("Connected to BTC price feed")
        while True:
            msg = await ws.recv()
            now = time.time() * 1000  # current local time in ms

            try:
                data = json.loads(msg)

                # Ensure 'p' exists and price is positive
                if "p" not in data or "T" not in data:
                    continue

                price = float(data["p"])
                if price <= 0:
                    continue

                exchange_time = data["T"]  # Binance server trade time in ms
                latency = now - exchange_time  # real latency in ms

                print(f"BTC Price: {price:.2f} | Latency: {latency:.2f} ms")

            except (json.JSONDecodeError, KeyError, ValueError):
                continue

asyncio.run(main())