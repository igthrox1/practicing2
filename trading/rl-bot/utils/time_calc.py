import time

def time_left(ts):
    if ts is None:
        return None
    diff = int(ts - time.time())
    if diff <= 0:
        return "00:00:00"
    h, r = divmod(diff, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"