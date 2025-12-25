import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# =========================
# PUT YOUR TESTNET KEYS
# =========================
API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"
BASE_URL = "https://testnet.binancefuture.com"

# ------------------------
# Sign parameters for Binance
# ------------------------
def sign_params(params, secret):
    query_string = urlencode(params)
    signature = hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params

# ------------------------
# Set leverage for a symbol
# ------------------------
def set_leverage(symbol: str, leverage: int):
    params = {
        "symbol": symbol,
        "leverage": leverage,
        "timestamp": int(time.time() * 1000)
    }
    signed = sign_params(params, API_SECRET)
    headers = {"X-MBX-APIKEY": API_KEY}
    url = BASE_URL + "/fapi/v1/leverage"
    response = requests.post(url, params=signed, headers=headers)
    print("Set leverage:", response.status_code, response.json())

# ------------------------
# Place MARKET order (BUY/LONG or SELL/SHORT) using USDT amount
# ------------------------
def place_order(symbol: str, side: str, usdt_amount: float, leverage: int):
    # 1️⃣ Set leverage
    set_leverage(symbol, leverage)

    # 2️⃣ Get current mark price
    price_url = BASE_URL + f"/fapi/v1/premiumIndex?symbol={symbol}"
    resp = requests.get(price_url)
    mark_price = float(resp.json()["markPrice"])
    print(f"Mark price: {mark_price}")

    # 3️⃣ Calculate quantity based on USDT amount and leverage
    quantity = round((usdt_amount * leverage) / mark_price, 3)  # round to 3 decimals
    print(f"Order quantity: {quantity}")

    # 4️⃣ Place MARKET order
    params = {
        "symbol": symbol,
        "side": side.upper(),  # BUY or SELL
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }
    signed_params = sign_params(params, API_SECRET)
    headers = {"X-MBX-APIKEY": API_KEY}
    order_url = BASE_URL + "/fapi/v1/order"
    response = requests.post(order_url, params=signed_params, headers=headers)
    print(f"{side.upper()} order response:", response.status_code, response.json())
    
# ------------------------
# Example usage
# ------------------------
symbol = "BTCUSDT"
usdt_amount = 50      # you want to trade 50 USDT
leverage = 15         # 10x leverage

# Place LONG
place_order(symbol, "SELL", usdt_amount, leverage)

# Place SHORT
# place_order(symbol, "SELL", usdt_amount, leverage)