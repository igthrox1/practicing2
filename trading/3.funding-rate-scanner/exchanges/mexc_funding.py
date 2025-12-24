import asyncio
import websockets
import aiohttp
import json
import time
from datetime import timedelta

WS_URL = "wss://contract.mexc.com/edge"
REST_URL = "https://contract.mexc.com/api/v1/contract/funding_rate"

# -------------------------------
# Fetch next funding settle time
# -------------------------------
async def fetch_next_settle(symbol: str) -> float | None:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{REST_URL}/{symbol}", timeout=5) as resp:
                res = await resp.json()
                data = res.get("data")
                if data and "nextSettleTime" in data:
                    return int(data["nextSettleTime"]) / 1000
        except Exception as e:
            print("MEXC REST error:", e)
    return None

# -------------------------------
# Countdown task (1 second tick)
# -------------------------------
async def countdown(symbol: str, state: dict):
    while True:
        if state["rate"] is not None and state["next_ts"] is not None:
            diff = max(state["next_ts"] - time.time(), 0)
            td = timedelta(seconds=int(diff))
            h, r = divmod(td.seconds, 3600)
            m, s = divmod(r, 60)
            state["time_left"] = f"{h:02d}:{m:02d}:{s:02d}"
        await asyncio.sleep(1)

# -------------------------------
# WebSocket funding stream
# -------------------------------
async def fetch_funding_rate(symbol: str, state: dict):
    # start countdown task
    asyncio.create_task(countdown(symbol, state))

    # get initial next settle
    state["next_ts"] = await fetch_next_settle(symbol)

    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=10) as ws:
                await ws.send(json.dumps({
                    "method": "sub.funding.rate",
                    "param": {"symbol": symbol},
                    "gzip": False
                }))
                print(f"Connected to MEXC WS for {symbol}")

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("channel") == "push.funding.rate":
                        state["rate"] = f"{float(data['data']['rate']):.6f}"
                        # update next settle dynamically
                        state["next_ts"] = await fetch_next_settle(symbol)

        except websockets.exceptions.ConnectionClosed:
            print("MEXC WS reconnecting...")
            await asyncio.sleep(2)
        except Exception as e:
            print("MEXC error:", e)
            await asyncio.sleep(3)