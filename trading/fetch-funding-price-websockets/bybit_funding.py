import asyncio
import websockets
import json
import time
from datetime import timedelta

URL = "wss://stream.bybit.com/v5/public/linear"

async def main():
    last_funding_rate = None
    last_next_funding = None

    async with websockets.connect(URL, ping_interval=20) as ws:
        print("Connected to Bybit WebSocket")

        # Subscribe to ticker stream for BTCUSDT
        await ws.send(json.dumps({
            "op": "subscribe",
            "args": ["tickers.BTCUSDT"]
        }))
        print("Subscribed to BTCUSDT ticker")

        while True:
            try:
                #start_time = time.time()
                msg = await ws.recv()
                #receive_time = time.time()

                #latency_ms = (receive_time - start_time) * 1000  # real latency

                data = json.loads(msg)

                # Valid ticker data check
                if "data" not in data:
                    continue

                ticker = data["data"][0] if isinstance(data["data"], list) else data["data"]

                # Update cached values only if present
                if "fundingRate" in ticker and ticker["fundingRate"] != "":
                    last_funding_rate = ticker["fundingRate"]

                if "nextFundingTime" in ticker and ticker["nextFundingTime"] not in (None, "", "0"):
                    last_next_funding = int(ticker["nextFundingTime"])

                # Calculate time left if we have timestamp
                if last_next_funding:
                    now = time.time()
                    diff = max((last_next_funding / 1000) - now, 0)
                    td = timedelta(seconds=int(diff))
                    hours, remainder = divmod(td.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_left = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    time_left = "N/A"

                print(
                    f"Bybit BTCUSDT | "
                    f"Funding Rate: {last_funding_rate} | "
                    f"Time Left: {time_left} | "
                    #f"Latency: {latency_ms:.2f} ms"
                )

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, reconnecting...")
                await asyncio.sleep(2)
            except Exception as e:
                print("Error:", e)
                await asyncio.sleep(2)
            except KeyboardInterrupt:
                print("Successfully program closed")
asyncio.run(main())