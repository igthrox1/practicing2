import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

BASE_URL = "https://testnet.binancefuture.com"
API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"



def sign_params(params, secret):
    query_string = urlencode(params)
    signature = hmac.new(
        secret.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params


def get_position_qty(symbol):
    params = {
        "timestamp": int(time.time() * 1000)
    }
    signed = sign_params(params, API_SECRET)
    headers = {"X-MBX-APIKEY": API_KEY}

    url = BASE_URL + "/fapi/v2/positionRisk"
    res = requests.get(url, headers=headers, params=signed).json()

    for p in res:
        if p["symbol"] == symbol:
            amt = float(p["positionAmt"])
            if amt != 0:
                print(f"📌 Position found: {amt}")
                return amt

    print("❌ No open position")
    return 0


def close_position(symbol):
    amt = get_position_qty(symbol)

    if amt == 0:
        return

    side = "SELL" if amt > 0 else "BUY"

    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": abs(amt),
        "reduceOnly": True,
        "timestamp": int(time.time() * 1000)
    }

    signed = sign_params(params, API_SECRET)
    headers = {"X-MBX-APIKEY": API_KEY}

    url = BASE_URL + "/fapi/v1/order"
    res = requests.post(url, headers=headers, params=signed)

    print("✅ Close order response:")
    print(res.json())


# ===== RUN HERE =====
if __name__ == "__main__":
    close_position("BTCUSDT")