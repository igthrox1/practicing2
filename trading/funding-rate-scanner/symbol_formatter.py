def format_symbol(exchange, coin):
    coin = coin.upper()

    if exchange == "binance":
        return f"{coin}USDT"

    if exchange == "bybit":
        return f"{coin}USDT"

    if exchange == "mexc":
        return f"{coin}_USDT"

    raise ValueError("Unsupported exchange")
