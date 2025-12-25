import time
import hmac
import hashlib
import requests
import json
import websocket
from urllib.parse import urlencode

# =========================
# BINANCE TESTNET DETAILS
# =========================
API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"

BASE_URL = "https://testnet.binancefuture.com"
SYMBOL = "BTCUSDT"

entry_price = None
position_qty = None

# =========================
# SIGN FUNCTION
# =========================
def sign_params(params):
    query_string = urlencode(params)
    signature = hmac.new(
        API_SECRET.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params

# =========================
# FETCH POSITION DETAILS
# =========================
def fetch_position():
    global entry_price, position_qty

    params = {
        "timestamp": int(time.time() * 1000)
    }

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    signed = sign_params(params)

    url = BASE_URL + "/fapi/v2/positionRisk"
    response = requests.get(url, headers=headers, params=signed)

    positions = response.json()

    for pos in positions:
        if pos["symbol"] == SYMBOL and float(pos["positionAmt"]) != 0:
            entry_price = float(pos["entryPrice"])
            position_qty = float(pos["positionAmt"])

            side = "LONG" if position_qty > 0 else "SHORT"
            print(f"✅ Position Found | {side}")
            print(f"Entry Price: {entry_price}")
            print(f"Quantity: {position_qty}")
            return

    print("❌ No open position found")
    exit()

# =========================
# WEBSOCKET PNL CALC
# =========================
def on_message(ws, message):
    data = json.loads(message)
    mark_price = float(data["p"])

    if position_qty > 0:
        pnl = (mark_price - entry_price) * position_qty
        side = "LONG"
    else:
        pnl = (entry_price - mark_price) * abs(position_qty)
        side = "SHORT"

    print(
        f"{side} | Mark: {mark_price:.2f} | Entry: {entry_price} | Qty: {position_qty} | PnL: {pnl:.4f} USDT"
    )

def on_open(ws):
    print("📡 Connected to Mark Price WebSocket")

def on_close(ws):
    print("🔌 WebSocket Closed")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    fetch_position()

    ws_url = f"wss://stream.binancefuture.com/ws/{SYMBOL.lower()}@markPrice@1s"

    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_open=on_open,
        on_close=on_close
    )

    ws.run_forever()