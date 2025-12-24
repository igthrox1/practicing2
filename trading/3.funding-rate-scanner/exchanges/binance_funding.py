# exchanges/binance_funding.py

import asyncio
import websockets
import json

URL = "wss://fstream.binance.com/ws/{}@markPrice"

async def fetch_funding_rate(symbol: str, state: dict):
    """
    Fetch Binance funding rate and next funding timestamp.
    Updates shared state only.
    """
    while True:
        try:
            async with websockets.connect(
                URL.format(symbol.lower()),
                ping_interval=20
            ) as ws:

                print(f"Connected to Binance WS for {symbol}")

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    # Funding rate
                    if data.get("r") is not None:
                        state["rate"] = float(data["r"])

                    # Next funding timestamp (ms → sec)
                    if data.get("T"):
                        state["next_ts"] = int(data["T"]) / 1000

        except websockets.exceptions.ConnectionClosed:
            print("Binance WS reconnecting...")
            await asyncio.sleep(2)

        except Exception as e:
            print("Binance error:", e)
            await asyncio.sleep(3)