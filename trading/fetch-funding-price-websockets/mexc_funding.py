import asyncio
import websockets
import json
import time
from datetime import timedelta
import aiohttp

WS_URL = "wss://contract.mexc.com/edge"
REST_URL = "https://contract.mexc.com/api/v1/contract/funding_rate"

# Fetch next funding timestamp from REST
async def fetch_next_settle(symbol: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{REST_URL}/{symbol}", timeout=5) as resp:
                result = await resp.json()
                data = result.get("data")

                if data and "nextSettleTime" in data:
                    return int(data["nextSettleTime"]) / 1000
        except Exception as e:
            print("Error fetching next settle:", e)
    return None 

# Live funding rate via WebSocket
async def mexc_funding_rate(symbol: str):
    while True:  # Reconnect loop
        try:
            next_settle_ts = await fetch_next_settle(symbol)
            async with websockets.connect(WS_URL, ping_interval=10) as ws:
                subscribe_msg = {
                    "method": "sub.funding.rate",
                    "param": {"symbol": symbol},
                    "gzip": False
                }
                await ws.send(json.dumps(subscribe_msg))
                print(f"Subscribed to MEXC funding rate for {symbol}\n")

                while True:
                    #start_time = time.time()
                    msg = await ws.recv()
                    #receive_time = time.time()

                    data = json.loads(msg)
                    if data.get("channel") == "push.funding.rate":
                        rate = float(data["data"]["rate"])

                        # Update next settle dynamically every message
                        next_settle_ts = await fetch_next_settle(symbol)

                        # Calculate time left
                        if next_settle_ts:
                            now = time.time()
                            diff = max(next_settle_ts - now, 0)
                            td = timedelta(seconds=int(diff))
                            hrs, rem = divmod(td.seconds, 3600)
                            mins, secs = divmod(rem, 60)
                            time_left_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                        else:
                            time_left_str = "N/A"

                        # Latency
                        #latency_ms = (receive_time - start_time) * 1000

                        print(
                            f"MEXC {symbol} | "
                            f"Funding Rate: {rate:+.6f} | "
                            f"Time Left: {time_left_str} | "
                           # f"Latency: {latency_ms:.2f} ms"
                        )

        except websockets.exceptions.ConnectionClosedOK:
            print("Connection closed by server, reconnecting...")
            await asyncio.sleep(1)
        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(3)
        except KeyboardInterrupt:
            print("succesfully the program closed ")
            break

asyncio.run(mexc_funding_rate('BTC_USDT'))