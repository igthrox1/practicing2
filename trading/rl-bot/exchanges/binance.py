import asyncio, websockets, json

URL = "wss://fstream.binance.com/ws/{}@markPrice"

async def binance_funding(symbol, state):
    while True:
        try:
            async with websockets.connect(URL.format(symbol.lower())) as ws:
                while True:
                    msg = json.loads(await ws.recv())

                    if msg.get("r"):
                        state["rate"] = float(msg["r"])

                    if msg.get("T"):
                        state["next_ts"] = msg["T"] / 1000

        except Exception:
            await asyncio.sleep(2)