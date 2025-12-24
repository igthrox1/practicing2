# exchanges/bybit_funding.py

import asyncio
import websockets
import json

URL = "wss://stream.bybit.com/v5/public/linear"

async def fetch_funding_rate(symbol: str, state: dict):
    """
    Fetch Bybit funding rate and next funding timestamp.
    Updates shared state only.
    """
    while True:
        try:
            async with websockets.connect(URL, ping_interval=20) as ws:
                print(f"Connected to Bybit WS for {symbol}")

                await ws.send(json.dumps({
                    "op": "subscribe",
                    "args": [f"tickers.{symbol}"]
                }))

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    if "data" not in data:
                        continue

                    ticker = data["data"][0] if isinstance(data["data"], list) else data["data"]

                    # Funding rate
                    if ticker.get("fundingRate"):
                        state["rate"] = float(ticker["fundingRate"])

                    # Next funding timestamp (ms → sec)
                    if ticker.get("nextFundingTime"):
                        state["next_ts"] = int(ticker["nextFundingTime"]) / 1000

        except websockets.exceptions.ConnectionClosed:
            print("Bybit WS reconnecting...")
            await asyncio.sleep(2)

        except Exception as e:
            print("Bybit error:", e)
            await asyncio.sleep(3)