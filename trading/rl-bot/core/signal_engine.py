from itertools import combinations

MIN_SPREAD = 0.0005

def compute_hedged_signals(state: dict, min_spread: float = MIN_SPREAD):
    signals = []
    exchanges = list(state.keys())

    for ex1, ex2 in combinations(exchanges, 2):
        r1 = state[ex1].get("rate")
        r2 = state[ex2].get("rate")

        if r1 is None or r2 is None:
            continue

        spread = abs(r1 - r2)

        if spread >= min_spread:
            if r1 < r2:
                signals.append({
                    "long": ex1,
                    "short": ex2,
                    "spread": spread,
                })
            else:
                signals.append({
                    "long": ex2,
                    "short": ex1,
                    "spread": spread,
                })
    return signals