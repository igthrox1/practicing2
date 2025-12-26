def get_user_config():
    coins = input("Enter coins (comma separated, ex: BTC,ETH): ").upper().split(",")
    exchanges = input("Enter exchanges (binance,bybit,mexc): ").lower().split(",")

    usdt = float(input("Enter USDT amount per leg: "))

    return {
        "coins": [c.strip() for c in coins],
        "exchanges": [e.strip() for e in exchanges],
        "usdt": usdt
    }