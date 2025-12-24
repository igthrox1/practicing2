import asyncio
from rich.live import Live

from ui.live_table import make_table
from exchanges import binance_funding, bybit_funding, mexc_funding

state = {}

async def main():
    coin = input("Enter coin (BTC/ETH/etc): ").strip().upper()
    exchanges_input = input(
        "Enter exchanges (comma separated, binance/bybit/mexc): "
    ).lower().split(",")

    tasks = []

    for ex in exchanges_input:
        ex = ex.strip()

        # 🔑 unified state structure
        state[ex] = {
            "rate": None,
            "next_ts": None
        }

        if ex == "binance":
            tasks.append(
                asyncio.create_task(
                    binance_funding.fetch_funding_rate(coin + "USDT", state[ex])
                )
            )

        elif ex == "bybit":
            tasks.append(
                asyncio.create_task(
                    bybit_funding.fetch_funding_rate(coin + "USDT", state[ex])
                )
            )

        elif ex == "mexc":
            tasks.append(
                asyncio.create_task(
                    mexc_funding.fetch_funding_rate(coin + "_USDT", state[ex])
                )
            )

        else:
            print(f"Exchange '{ex}' not supported")

    # 🔴 keep tasks alive implicitly
    with Live(make_table(state), refresh_per_second=1) as live:
        while True:
            live.update(make_table(state))
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram stopped cleanly")