import asyncio
from rich.live import Live
from strategy.funding_arbitrage import compute_arbitrage_signals
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
        state[ex] = {"rate": None, "next_ts": None}

        if ex == "binance":
            tasks.append(asyncio.create_task(binance_funding.fetch_funding_rate(coin + "USDT", state[ex])))
        elif ex == "bybit":
            tasks.append(asyncio.create_task(bybit_funding.fetch_funding_rate(coin + "USDT", state[ex])))
        elif ex == "mexc":
            tasks.append(asyncio.create_task(mexc_funding.fetch_funding_rate(coin + "_USDT", state[ex])))
        else:
            print(f"Exchange '{ex}' not supported")

    last_signals = []

    # Live table
    with Live(make_table(state), refresh_per_second=1) as live:
        while True:
            live.update(make_table(state))

            # Only compute signals if all exchanges have rates
            if all(info.get("rate") is not None for info in state.values()):
                signals = compute_arbitrage_signals(state)
            else:
                signals = []

            # Only print/update if signals changed
            if signals != last_signals:
                last_signals = signals

                # Clear previous CLI lines
                print("\033[F\033[K" * 10, end="")

                if signals:
                    for s in signals:
                        print(f"[ARBITRAGE] Long {s['long']} | Short {s['short']} | Spread: {s['spread']:.6f}")
                else:
                    print("[ARBITRAGE] No active signals")

            # ✅ Do not print anything if signals are unchanged
            await asyncio.sleep(1)


asyncio.run(main())
    