import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"

BASE_URL = "https://testnet.binancefuture.com"


def sign_params(params, secret):
    query_string = urlencode(params)
    signature = hmac.new(
        secret.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params


def get_funding_history(symbol):
    params = {
        "incomeType": "FUNDING_FEE",
        "timestamp": int(time.time() * 1000)
    }

    signed_params = sign_params(params, API_SECRET)

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    url = BASE_URL + "/fapi/v1/income"
    response = requests.get(url, headers=headers, params=signed_params)

    print("HTTP Status:", response.status_code)
    data = response.json()

    print("\n===== FULL FUNDING RESPONSE =====")
    for item in data:
        if item["symbol"] == symbol:
            print(item)


get_funding_history("BTCUSDT")