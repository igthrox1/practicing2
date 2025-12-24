# exchanges/binance_funding.py
import asyncio
import websockets
import json
import time
from datetime import timedelta

URL = "wss://fstream.binance.com/ws/{}@markPrice"

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
    """Fetch Binance live funding rate and next funding timestamp"""
    # Start countdown
    asyncio.create_task(countdown(symbol, state))

    async with websockets.connect(URL.format(symbol.lower()), ping_interval=20) as ws:
        print(f"Connected to Binance WS for {symbol}")
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            # Funding rate
            state["rate"] = data.get("r")
            # Next funding timestamp (T)
            next_ts_ms = data.get("T")
            if next_ts_ms:
                state["next_ts"] = int(next_ts_ms) / 1000