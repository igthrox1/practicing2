# exchanges/bybit_funding.py
import asyncio
import websockets
import json
import time
from datetime import timedelta

URL = "wss://stream.bybit.com/v5/public/linear"

async def countdown(symbol: str, state: dict):
    """Update time left every second"""
    while True:
        if state["rate"] is not None and state["next_ts"] is not None:
            diff = max(state["next_ts"] - time.time(), 0)
            td = timedelta(seconds=int(diff))
            h, rem = divmod(td.seconds, 3600)
            m, s = divmod(rem, 60)
            state["time_left"] = f"{h:02d}:{m:02d}:{s:02d}"
        await asyncio.sleep(1)

async def fetch_funding_rate(symbol: str, state: dict):
    """Fetch Bybit live funding rate and next funding timestamp"""
    # Start countdown
    asyncio.create_task(countdown(symbol, state))

    async with websockets.connect(URL, ping_interval=20) as ws:
        print(f"Connected to Bybit WS for {symbol}")
        # Subscribe to ticker
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

            # Update funding rate if present
            if "fundingRate" in ticker and ticker["fundingRate"] != "":
                state["rate"] = ticker["fundingRate"]

            # Update next funding timestamp if present
            if "nextFundingTime" in ticker and ticker["nextFundingTime"] not in (None, "", "0"):
                state["next_ts"] = int(ticker["nextFundingTime"]) / 1000