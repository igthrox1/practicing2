import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# =========================
# BINANCE FUTURES TESTNET KEYS
# =========================
API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"

BASE_URL = "https://testnet.binancefuture.com"

# =========================
# SIGN REQUEST
# =========================
def sign_params(params, secret):
    query_string = urlencode(params)
    signature = hmac.new(
        secret.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params

# =========================
# PLACE BUY (LONG) ORDER
# =========================
def place_long_order():
    print("🚀 Placing LONG (BUY) order...")

    params = {
        "symbol": "BTCUSDT",     # Change coin if needed
        "side": "BUY",           # BUY = LONG
        "type": "MARKET",        # Market order
        "quantity": 1,       # Contract size
        "timestamp": int(time.time() * 1000)
    }

    signed_params = sign_params(params, API_SECRET)

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    url = BASE_URL + "/fapi/v1/order"

    response = requests.post(url, headers=headers, params=signed_params)

    print("HTTP Status:", response.status_code)
    print("Response:")
    print(response.json())

# =========================
# RUN
# =========================
if __name__ == "__main__":
    place_long_order()