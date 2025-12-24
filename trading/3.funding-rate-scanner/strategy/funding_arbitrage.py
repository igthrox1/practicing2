from itertools import combinations

MIN_SPREAD = 0.0005  # Minimum spread to consider, adjust as needed

def compute_arbitrage_signals(state: dict, min_spread: float = MIN_SPREAD):
    """
    Check all exchange pairs and return arbitrage signals.
    
    Args:
        state (dict): Dictionary of exchanges with their 'rate' and 'next_ts'.
        min_spread (float): Minimum difference between rates to trigger a signal.
    
    Returns:
        List[dict]: Each dict contains pair, spread, and trade directions.
    """
    signals = []
    exchanges = list(state.keys())

    # Check all unique pairs
    for ex1, ex2 in combinations(exchanges, 2):
        info1 = state[ex1]
        info2 = state[ex2]

        if info1.get("rate") is None or info2.get("rate") is None:
            continue  # skip if rate missing

        rate1 = float(info1["rate"])
        rate2 = float(info2["rate"])

        spread = abs(rate1 - rate2)

        if spread >= min_spread:
            # Determine long/short
            if rate1 < rate2:
                signal = {
                    "long": ex1,
                    "short": ex2,
                    "spread": spread*100,
                    "rate_long": rate1,
                    "rate_short": rate2,
                }
            else:
                signal = {
                    "long": ex2,
                    "short": ex1,
                    "spread": spread*100,
                    "rate_long": rate2,
                    "rate_short": rate1,
                }
            signals.append(signal)
    return signals