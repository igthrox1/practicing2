import time
from datetime import timedelta

def run_full_timer(start_time_str, target_time_str):
    """
    Simulates a full clock countdown from start_time to target_time.
    start_time_str: "HH:MM:SS" -> starting time
    target_time_str: "HH:MM:SS" -> target time to execute
    """
    # Parse start and target times
    h, m, s = map(int, start_time_str.split(":"))
    target_h, target_m, target_s = map(int, target_time_str.split(":"))
    
    current_time = timedelta(hours=h, minutes=m, seconds=s)
    target_time = timedelta(hours=target_h, minutes=target_m, seconds=target_s)
    
    print(f"⏱ Timer started at {start_time_str}, target is {target_time_str}")
    
    while current_time > target_time:
        hrs, rem = divmod(current_time.seconds, 3600)
        mins, secs = divmod(rem, 60)
        print(f"Timer: {hrs:02d}:{mins:02d}:{secs:02d}", end="\r")
        time.sleep(1)
        current_time -= timedelta(seconds=1)
    
    print(f"\n🚀 Target time {target_time_str} reached! Execute order now!")

# -------------------------
# Example usage
# -------------------------
start_time = "00:01:05"  # simulated start
target_time = "00:00:03"  # fire order at this simulated time
run_full_timer(start_time, target_time)