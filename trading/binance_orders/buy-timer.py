import time
import hmac
import hashlib
import requests
import websocket
import json
from urllib.parse import urlencode
from datetime import timedelta

# =========================
# PUT YOUR TESTNET KEYS
# =========================
API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"
BASE_URL = "https://testnet.binancefuture.com"

# -------------------------
# Helper: Sign params
# -------------------------
def sign_params(params):
    query_string = urlencode(params)
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params

# -------------------------
# Place MARKET order
# -------------------------
def place_order(symbol, side, quantity):
    url = BASE_URL + "/fapi/v1/order"
    params = {
        "symbol": symbol,
        "side": side.upper(),  # BUY or SELL
        "type": "MARKET",
        "quantity": quantity,
        "positionSide": "BOTH",
        "timestamp": int(time.time() * 1000)
    }
    params = sign_params(params)
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.post(url, headers=headers, params=params)
    print(f"Order Response ({side}):", response.json())

# -------------------------
# WebSocket to get mark price

def get_mark_price(symbol):
    ws_url = f"wss://fstream.binance.com/ws/{symbol.lower()}@markPrice"
    mark_price = None

    def on_message(ws, message):
        nonlocal mark_price
        data = json.loads(message)
        mark_price = float(data['p'])  # current mark price
        ws.close()  # Close after getting one message

    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    ws.run_forever()
    return mark_price

# -------------------------
# Countdown to target time
# -------------------------
def run_full_timer(start_time_str, target_time_str, symbol, usdt_amount):
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
    
    print(f"\n🚀 Target time {target_time_str} reached! Executing LONG order...")

    # -------------------------
    # Fetch mark price to calculate quantity
    # -------------------------
    mark_price = get_mark_price(symbol)
    quantity = round(usdt_amount / mark_price, 3)
    print(f"Mark Price: {mark_price}, Calculated Quantity: {quantity}")

    # -------------------------
    # Place LONG order
    # -------------------------
    place_order(symbol, "BUY", quantity)
    print("✅ LONG order submitted!")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    symbol = "BTCUSDT"
    usdt_amount = 1000 # Buy $10 worth
    start_time = "00:00:14"
    target_time = "00:00:03"
    
    run_full_timer(start_time, target_time, symbol, usdt_amount)