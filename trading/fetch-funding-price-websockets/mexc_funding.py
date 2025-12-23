import asyncio
import json
import websockets

WS_URL = "wss://contract.mexc.com/edge"

async def mexc_funding_rate(symbol: str):
    async with websockets.connect(WS_URL) as ws:

        subscribe_msg = {
            "method": "sub.funding.rate",
            "param": {
                "symbol": symbol
            },
            "gzip": False
        }

        await ws.send(json.dumps(subscribe_msg))
        print(f"Subscribed to MEXC funding rate for {symbol}\n")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data.get("channel") == "push.funding.rate":
                rate = data["data"]["rate"]
                print(f"MEXC {symbol} funding rate: {rate:+.6f}")

async def main():
    try:
        await mexc_funding_rate("BTC_USDT")
    except asyncio.CancelledError:
        print("\nStopped by user 👋")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited cleanly ✨")