from rich.table import Table
from utils.time_calc import format_time_left

def make_table(state: dict) -> Table:
    table = Table(title="Live Funding Rates")

    table.add_column("Exchange", style="cyan", no_wrap=True)
    table.add_column("Rate", style="green")
    table.add_column("Time Left", style="magenta")

    for ex, info in state.items():
        rate = info.get("rate")
        next_ts = info.get("next_ts")

        # format rate
        if rate is not None:
            rate = f"{float(rate):.6f}"
        else:
            rate = "-"

        # format time left using helper
        time_left = format_time_left(next_ts)

        table.add_row(ex.capitalize(), rate, time_left)

    return table