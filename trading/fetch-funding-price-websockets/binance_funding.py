import asyncio
import websockets
import json
import time
from datetime import  timedelta

# Binance mark price + funding rate WebSocket
URL = "wss://fstream.binance.com/ws/btcusdt@markPrice"

async def main():
    async with websockets.connect(URL, ping_interval=20) as ws:
        print("Connected to Binance live funding + mark price feed")
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                # Mark price
                #mark_price = data.get("p")  # string, exact
                # Funding rate (raw, full precision)
                funding_rate = data.get("r")  # string
                # Next funding timestamp
                next_funding_ms = int(data.get("T", 0))
                next_funding_sec = next_funding_ms / 1000
                # Time left calculation
                time_left_sec = max(next_funding_sec - time.time(), 0)
                time_left_td = timedelta(seconds=int(time_left_sec))
                # Format HH:MM:SS
                hours, remainder = divmod(time_left_td.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_left_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                # Latency in ms
                #latency_ms = (receive_time - start_time) * 1000

                print(
                    #f"BTCUSDT Mark Price: {mark_price} | "
                    f"Funding Rate: {funding_rate} | "
                    f"Time Left: {time_left_str} | "
                    #f"Latency: {latency_ms:.2f} ms"
                )

            except (json.JSONDecodeError, KeyError, ValueError):
                continue
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket closed, reconnecting...")
                await asyncio.sleep(2)
            except Exception as e:
                print("Error:", e)
                await asyncio.sleep(5)
            except KeyboardInterrupt:
                print("Succesfully Exited the program")

asyncio.run(main())