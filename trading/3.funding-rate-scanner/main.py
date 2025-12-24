import asyncio
from rich.live import Live
from rich.table import Table
from exchanges import binance_funding, bybit_funding, mexc_funding

# Shared state for all exchanges
state = {}

# Function to create the table
def make_table():
    table = Table(title="Live Funding Rates")
    table.add_column("Exchange", style="cyan", no_wrap=True)
    table.add_column("Rate", style="green")
    table.add_column("Time Left", style="magenta")
    
    for ex, info in state.items():
        rate = info.get("rate")
        time_left = info.get("time_left", "-")
        if rate is None:
            rate = "-"
        else:
            # Ensure 6 decimal places
            rate = f"{float(rate):.6f}"
        table.add_row(ex.capitalize(), rate, time_left)
    
    return table

async def main():
    # Get user input
    coin = input("Enter coin (BTC/ETH/etc): ").strip().upper()
    exchanges_input = input("Enter exchanges (comma separated, binance/bybit/mexc): ").lower().split(",")
    tasks = []
    
    # Initialize state and start tasks per exchange
    for ex in exchanges_input:
        state[ex] = {"rate": None, "time_left": None}
        if ex == "binance":
            tasks.append(asyncio.create_task(binance_funding.fetch_funding_rate(coin + "USDT", state[ex])))
        elif ex == "bybit":
            tasks.append(asyncio.create_task(bybit_funding.fetch_funding_rate(coin + "USDT", state[ex])))
        elif ex == "mexc":
            tasks.append(asyncio.create_task(mexc_funding.fetch_funding_rate(coin + "_USDT", state[ex])))
        else:
            print(f"Exchange {ex} not supported")
    
    # Live table
    with Live(make_table(), refresh_per_second=1) as live:
        while True:
            live.update(make_table())
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram stopped cleanly")