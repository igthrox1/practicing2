# exchanges/mexc_funding.py

import asyncio
import websockets
import aiohttp
import json

WS_URL = "wss://contract.mexc.com/edge"
REST_URL = "https://contract.mexc.com/api/v1/contract/funding_rate"

# --------------------------------
# Fetch next funding settle time
# --------------------------------
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

# --------------------------------
# WebSocket funding stream
# --------------------------------
async def fetch_funding_rate(symbol: str, state: dict):
    # Initial next funding time
    state["next_ts"] = await fetch_next_settle(symbol)

    while True:
        try:
            async with websockets.connect(
                WS_URL,
                ping_interval=10
            ) as ws:

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
                        # Funding rate (RAW float)
                        state["rate"] = float(data["data"]["rate"])

                        # Refresh next settle (MEXC requirement)
                        state["next_ts"] = await fetch_next_settle(symbol)

        except websockets.exceptions.ConnectionClosed:
            print("MEXC WS reconnecting...")
            await asyncio.sleep(2)

        except Exception as e:
            print("MEXC error:", e)
            await asyncio.sleep(3)