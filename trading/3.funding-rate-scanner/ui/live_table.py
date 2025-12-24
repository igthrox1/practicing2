from rich.table import Table
from utils.time_calc import format_time_left


def make_table(state: dict) -> Table:
    table = Table(title="Live Funding Rates")

    table.add_column("Exchange", style="cyan", no_wrap=True)
    table.add_column("Rate", style="green")
    table.add_column("Time Left", style="magenta")

    # Stable ordering
    for ex in sorted(state.keys()):
        info = state[ex]

        rate = info.get("rate")
        next_ts = info.get("next_ts")

        # Safe rate formatting
        try:
            rate_str = f"{float(rate)*100:.6f}%" if rate is not None else "-"
        except (ValueError, TypeError):
            rate_str = "-"

        time_left = format_time_left(next_ts)

        table.add_row(ex.capitalize(), rate_str, time_left)

    return table