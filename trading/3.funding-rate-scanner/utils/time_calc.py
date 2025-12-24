# helpers/time_utils.py

import time

def format_time_left(ts: float | None) -> str:
    """
    Convert a future UNIX timestamp into HH:MM:SS remaining.
    Safe for all exchanges.
    """
    if ts is None:
        return "-"

    try:
        diff = int(ts - time.time())
    except Exception:
        return "-"

    if diff <= 0:
        return "00:00:00"

    hours, rem = divmod(diff, 3600)
    minutes, seconds = divmod(rem, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"