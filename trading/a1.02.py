import asyncio
import json
import aiohttp
import websockets
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from decimal import Decimal, ROUND_DOWN
import ntplib
from datetime import datetime

# =========================
# TIME SYNC CORRECTION
# =========================
TIME_OFFSET = 0  # Will be set after NTP sync
# MANUAL ADJUSTMENT: Add seconds here if your code is still late
# Example: If phone shows 06:55:30 but code shows 06:55:25, set MANUAL_ADJUST = -5
MANUAL_ADJUST = 0  # Change this value to match your phone!

def get_accurate_time():
    """Get accurate time using NTP/Exchange sync offset + Manual Adjustment"""
    return time.time() + TIME_OFFSET + MANUAL_ADJUST

# =========================
# LOGGING SETUP
# =========================
LOG_FILE = "trade_audit.log"

def audit_log(msg, also_print=True):
    """Write message to file and optionally print to console"""
    curr_time = get_accurate_time()
    ts_full = datetime.fromtimestamp(curr_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    ts_short = datetime.fromtimestamp(curr_time).strftime('%H:%M:%S.%f')[:-3]
    
    log_entry = f"[{ts_full}] {msg}"
    
    # Always append to file
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

    # Optionally print to terminal
    if also_print:
        print(f"[{ts_short}] 📝 AUDIT: {msg}")

def sync_time_with_ntp():
    """Sync system time with NTP servers and calculate offset"""
    global TIME_OFFSET
    try:
        ntp_client = ntplib.NTPClient()
        # Try multiple NTP servers
        ntp_servers = ['time.google.com', 'pool.ntp.org', 'time.windows.com']
        
        for server in ntp_servers:
            try:
                response = ntp_client.request(server, version=3, timeout=5)
                ntp_time = response.tx_time
                system_time = time.time()
                TIME_OFFSET = ntp_time - system_time
                
                audit_log(f"✅ Time synced with {server}")
                audit_log(f"   System time: {datetime.fromtimestamp(system_time).strftime('%H:%M:%S.%f')[:-3]}")
                audit_log(f"   NTP time:    {datetime.fromtimestamp(ntp_time).strftime('%H:%M:%S.%f')[:-3]}")
                audit_log(f"   Offset:      {TIME_OFFSET:.3f}s {'(AHEAD)' if TIME_OFFSET > 0 else '(BEHIND)'}")
                
                if abs(TIME_OFFSET) > 1:
                    audit_log(f"⚠️  WARNING: Your system clock is {abs(TIME_OFFSET):.1f} seconds {'ahead' if TIME_OFFSET > 0 else 'behind'}!")
                
                return True
            except Exception as e:
                print(f"Failed to sync with {server}: {e}")
                continue
        
        print("❌ Could not sync with any NTP server, using system time")
        TIME_OFFSET = 0
        return False
    except Exception as e:
        print(f"❌ NTP sync error: {e}")
        TIME_OFFSET = 0
        return False

def get_binance_server_time():
    """Get accurate server time from Binance"""
    global TIME_OFFSET
    try:
        # Get Binance server time
        response = requests.get("https://fapi.binance.com/fapi/v1/time", timeout=3)
        data = response.json()
        server_time = data["serverTime"] / 1000  # Convert to seconds
        
        # Get local time
        local_time = time.time()
        
        # Calculate offset
        TIME_OFFSET = server_time - local_time
        
        print(f"✅ Synced with Binance server")
        print(f"   Server time offset: {TIME_OFFSET:.3f} seconds")
        print(f"   Manual adjustment: {MANUAL_ADJUST:+d} seconds")
        if abs(TIME_OFFSET) > 1:
            print(f"   ⚠️  WARNING: Your clock is {abs(TIME_OFFSET):.1f}s {'ahead' if TIME_OFFSET < 0 else 'behind'}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to sync with Binance: {e}")
        return False

def get_bybit_server_time():
    """Get accurate server time from Bybit"""
    global TIME_OFFSET
    try:
        # Get Bybit server time
        response = requests.get("https://api.bybit.com/v5/market/time", timeout=3)
        data = response.json()
        server_time = int(data["result"]["timeSecond"])  # Already in seconds
        
        # Get local time
        local_time = time.time()
        
        # Calculate offset
        TIME_OFFSET = server_time - local_time
        
        print(f"✅ Synced with Bybit server")
        print(f"   Server time offset: {TIME_OFFSET:.3f} seconds")
        print(f"   Manual adjustment: {MANUAL_ADJUST:+d} seconds")
        if abs(TIME_OFFSET) > 1:
            print(f"   ⚠️  WARNING: Your clock is {abs(TIME_OFFSET):.1f}s {'ahead' if TIME_OFFSET < 0 else 'behind'}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to sync with Bybit: {e}")
        return False

# =========================
# BINANCE WS (MARK + FUNDING)
# =========================
async def binance_ws(symbol, state):
    # Combined stream: bookTicker for BBO + markPrice for Funding/TimeSync
    base_url = "wss://stream.binancefuture.com/stream?streams="  # ✅ TESTNET
    streams = f"{symbol.lower()}@bookTicker/{symbol.lower()}@markPrice"
    url = base_url + streams
    
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                print(f"✅ Binance Combined WS connected ({symbol})")
                async for msg in ws:
                    res = json.loads(msg)
                    stream = res.get("stream")
                    d = res.get("data")
                    
                    if "bookticker" in stream.lower():
                        # Update BBO for calculations
                        state["binance"]["bid"] = float(d["b"])
                        state["binance"]["ask"] = float(d["a"])
                    
                    elif "markprice" in stream.lower():
                        # Update Display Price & Funding & Time
                        state["binance"]["price"] = float(d["p"])
                        state["binance"]["funding"] = float(d["r"]) * 100
                        state["binance"]["next_ts"] = int(d["T"])
                        
                        global TIME_OFFSET
                        ws_server_time = int(d["E"]) / 1000
                        TIME_OFFSET = ws_server_time - time.time()
        except Exception as e:
            print("Binance WS error:", e)
            await asyncio.sleep(0.5)

# =========================
# BYBIT WS (MARK + FUNDING)
# =========================
async def bybit_ws(symbol, state):
    url = "wss://stream.bybit.com/v5/public/linear"
    sub = {"op": "subscribe", "args": [f"tickers.{symbol}"]}
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                await ws.send(json.dumps(sub))
                print("✅ Bybit BBO WS connected")
                async for msg in ws:
                    d = json.loads(msg)
                    if "data" in d:
                        data = d["data"]
                        if "bid1Price" in data: state["bybit"]["bid"] = float(data["bid1Price"])
                        if "ask1Price" in data: state["bybit"]["ask"] = float(data["ask1Price"])
                        if "markPrice" in data: state["bybit"]["price"] = float(data["markPrice"])
                        if "fundingRate" in data: state["bybit"]["funding"] = float(data["fundingRate"]) * 100
                        if "nextFundingTime" in data: state["bybit"]["next_ts"] = int(data["nextFundingTime"])
        except Exception as e:
            print("Bybit WS error:", e)
            await asyncio.sleep(0.5)

# =========================
# MEXC REST (MARK + FUNDING)
# =========================
async def mexc_rest(symbol, state):
    price_url = f"https://contract.mexc.com/api/v1/contract/fair_price/{symbol}"
    funding_url = f"https://contract.mexc.com/api/v1/contract/funding_rate/{symbol}"
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(price_url) as r:
                    j = await r.json()
                    state["mexc"]["price"] = float(j["data"]["fairPrice"])
                async with session.get(funding_url) as r:
                    j = await r.json()
                    state["mexc"]["funding"] = float(j["data"]["fundingRate"]) * 100
                    state["mexc"]["next_ts"] = int(j["data"]["nextSettleTime"])
            except Exception as e:
                print("MEXC REST error:", e)
            await asyncio.sleep(1)

# =========================
# TIME LEFT (REAL EXCHANGE TIME)
# =========================
def time_left(ts):
    if not ts:
        return "--:--:--"
    
    # Convert timestamp from milliseconds to seconds
    ts_seconds = ts / 1000
    current_time = get_accurate_time()  # Use NTP-synced time
    diff = int(ts_seconds - current_time)
    
    # Debug: Print if time difference is unusual
    if diff < -3600 or diff > 28800:  # Less than -1 hour or more than 8 hours
        print(f"⚠️ WARNING: Unusual time difference: {diff}s (ts={ts}, current={current_time})")
    
    if diff <= 0:
        return "00:00:00"
    
    h = diff // 3600
    m = (diff % 3600) // 60
    s = diff % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# =========================
# FUNDING ARB SIGNAL
# =========================
def funding_arbitrage_signal(state, exchanges, min_spread):
    rates = {ex: state[ex]["funding"] for ex in exchanges if state[ex]["funding"] is not None}
    if len(rates) < 2:
        return None
    short_ex = max(rates, key=rates.get)
    long_ex = min(rates, key=rates.get)
    spread = rates[short_ex] - rates[long_ex]
    if spread < min_spread:
        return None
    return {"long": long_ex, "short": short_ex, "spread": spread}

# =========================
# BINANCE TESTNET EXECUTION
# =========================
BINANCE_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"
BINANCE_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"
BINANCE_URL = "https://testnet.binancefuture.com"

def binance_sign(params):
    qs = urlencode(params)
    sig = hmac.new(BINANCE_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params

def binance_set_leverage(symbol, lev):
    try:
        params = binance_sign({
            "symbol": symbol,
            "leverage": lev,
            "timestamp": int(get_accurate_time()*1000)  # Use NTP-synced time
        })
        r = requests.post(
            BINANCE_URL + "/fapi/v1/leverage",
            headers={"X-MBX-APIKEY": BINANCE_KEY},
            params=params,
            timeout=5
        )
        print(f"Binance leverage response: {r.status_code} - {r.text}")
        return r.json()
    except Exception as e:
        print(f"Binance leverage error: {e}")
        return {}

def get_binance_symbol_filters(symbol):
    """Fetch LOT_SIZE stepSize and PRICE_FILTER tickSize from Binance API"""
    try:
        url = BINANCE_URL + "/fapi/v1/exchangeInfo"
        r = requests.get(url, timeout=3)
        data = r.json()
        
        filters = {"step_size": "1", "tick_size": "0.01"}
        for s in data.get("symbols", []):
            if s["symbol"] == symbol:
                for f in s.get("filters", []):
                    if f["filterType"] == "LOT_SIZE":
                        filters["step_size"] = f["stepSize"]
                    if f["filterType"] == "PRICE_FILTER":
                        filters["tick_size"] = f["tickSize"]
                return filters
        return filters
    except Exception as e:
        print(f"⚠️ CRITICAL: Failed to fetch Binance filters: {e}")
        print(f"⚠️ Cannot continue without symbol info. Please check API connection.")
        return None  # ✅ Return None to signal failure


def round_step_size(quantity, step_size):
    """Round quantity to match stepSize precision (Floor)"""
    step_size = Decimal(str(step_size))
    quantity = Decimal(str(quantity))
    rounded = float(quantity.quantize(step_size, rounding=ROUND_DOWN))
    return rounded

def round_step_size_nearest(quantity, step_size):
    """Round quantity to match stepSize precision (Nearest) - Best for Hedging Parity"""
    from decimal import ROUND_HALF_UP
    step_size = Decimal(str(step_size))
    quantity = Decimal(str(quantity))
    rounded = float(quantity.quantize(step_size, rounding=ROUND_HALF_UP))
    return rounded

def round_price(price, tick_size):
    """Round price to match tickSize precision"""
    tick_size = Decimal(str(tick_size))
    price = Decimal(str(price))
    rounded = float(price.quantize(tick_size, rounding=ROUND_DOWN))
    return rounded

def binance_limit_order(symbol, side, qty, price, step_size, tick_size):
    for attempt in range(3):
        try:
            qty = round_step_size(qty, step_size)
            price = round_price(price, tick_size)
            params = binance_sign({
                "symbol": symbol,
                "side": side,
                "type": "LIMIT",
                "quantity": qty,
                "price": price,
                "timeInForce": "GTX",  # Post-Only
                "timestamp": int(get_accurate_time()*1000)
            })
            audit_log(f"Binance Limit Req: {side} {qty} @ {price} (Post-Only) | Attempt {attempt+1}")
            r = requests.post(BINANCE_URL + "/fapi/v1/order", headers={"X-MBX-APIKEY": BINANCE_KEY}, params=params, timeout=5)
            res = r.json()
            
            # Check for transient errors
            if "code" in res and res["code"] in [-1001, -1003, -1007, -1021]:
                audit_log(f"⚠️ Binance transient error {res['code']}: {res.get('msg')}. Retrying...")
                time.sleep(1)
                continue
                
            audit_log(f"Binance Limit Res: {json.dumps(res)}")
            return res
        except Exception as e:
            audit_log(f"💥 Binance limit order exception (Attempt {attempt+1}): {e}")
            if attempt < 2: time.sleep(1)
    return {}

def binance_cancel_order(symbol, order_id):
    try:
        params = binance_sign({
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(get_accurate_time()*1000)
        })
        r = requests.delete(BINANCE_URL + "/fapi/v1/order", headers={"X-MBX-APIKEY": BINANCE_KEY}, params=params, timeout=5)
        return r.json()
    except Exception as e:
        print(f"Binance cancel error: {e}")
        return {}

def binance_get_order(symbol, order_id):
    try:
        params = binance_sign({
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(get_accurate_time()*1000)
        })
        r = requests.get(BINANCE_URL + "/fapi/v1/order", headers={"X-MBX-APIKEY": BINANCE_KEY}, params=params, timeout=5)
        return r.json()
    except Exception as e:
        print(f"Binance get order error: {e}")
        return {}

def binance_order(symbol, side, qty, step_size):
    for attempt in range(3):
        try:
            qty = round_step_size(qty, step_size)
            params = binance_sign({
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": qty,
                "timestamp": int(get_accurate_time()*1000)
            })
            r = requests.post(BINANCE_URL + "/fapi/v1/order", headers={"X-MBX-APIKEY": BINANCE_KEY}, params=params, timeout=5)
            res = r.json()
            
            if "code" in res and res["code"] in [-1001, -1003, -1007, -1021]:
                audit_log(f"⚠️ Binance Market transient error {res['code']}: {res.get('msg')}. Retrying...")
                time.sleep(1)
                continue
                
            return res
        except Exception as e:
            print(f"Binance order error (Attempt {attempt+1}): {e}")
            if attempt < 2: time.sleep(1)
    return {}

# =========================
# BINANCE PNL FETCHER (NEW)
# =========================

async def get_binance_entry_info(session, symbol):
    """Fetch entry price and position size from Binance (Async)"""
    try:
        params = binance_sign({
            "symbol": symbol,
            "timestamp": int(get_accurate_time()*1000)
        })
        async with session.get(BINANCE_URL + "/fapi/v2/positionRisk", params=params, timeout=3) as r:
            if r.status == 200:
                data = await r.json()
                for pos in data:
                    if pos["symbol"] == symbol:
                        size = float(pos.get("positionAmt", 0))
                        if size != 0:
                            entry = float(pos.get("entryPrice", 0))
                            side = "LONG" if size > 0 else "SHORT"
                            return {"entry_price": entry, "size": abs(size), "side": side}
            return None
    except Exception as e:
        # audit_log(f"Binance entry info error: {e}")
        return None

async def get_bybit_entry_info(session, symbol):
    """Fetch entry price and position size from Bybit (Async)"""
    try:
        timestamp = str(int(get_accurate_time() * 1000))
        params = {"category": "linear", "symbol": symbol}
        signature = bybit_sign(params, timestamp, "")
        queryString = urlencode(sorted(params.items()))
        url = f"{BYBIT_URL}/v5/position/list?{queryString}"
        
        headers = {
            "X-BAPI-API-KEY": BYBIT_KEY,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": "5000",
        }
        
        async with session.get(url, headers=headers, timeout=5) as r:
            if r.status != 200: return None
            data = await r.json()
            if data.get("retCode") == 0:
                positions = data.get("result", {}).get("list", [])
                for pos in positions:
                    if pos.get("symbol") == symbol:
                        size = float(pos.get("size", 0))
                        if size != 0:
                            entry = float(pos.get("avgPrice") or pos.get("entryPrice", 0))
                            side = pos.get("side")
                            return {"entry_price": entry, "size": size, "side": side}
            return None
    except Exception as e:
        # audit_log(f"Bybit entry info exception: {e}")
        return None

# =========================
# BYBIT DEMO EXECUTION
# =========================
BYBIT_KEY = "hfE8R6aHfeEdGX18w7"
BYBIT_SECRET = "AYuExy9gfspxpTBWTZkyHIiyKz8vkdqVqnso"
BYBIT_URL = "https://api-demo.bybit.com"

def bybit_sign(params, timestamp, request_body=""):
    """CORRECT V5 signature for Bybit"""
    # Sort and stringify parameters alphabetically for GET requests
    param_str = ""
    if params:
        param_str = urlencode(sorted(params.items()))
    
    # Build signature payload
    recv_window = "5000"
    
    if request_body:  # POST request
        signature_payload = timestamp + BYBIT_KEY + recv_window + request_body
    else:  # GET request
        signature_payload = timestamp + BYBIT_KEY + recv_window + param_str
    
    # Generate HMAC-SHA256
    signature = hmac.new(
        bytes(BYBIT_SECRET, "utf-8"),
        bytes(signature_payload, "utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return signature
def bybit_set_leverage(symbol, lev):
    try:
        timestamp = str(int(get_accurate_time() * 1000))
        signature = bybit_sign({}, timestamp, "")
        
        headers = {
            "X-BAPI-API-KEY": BYBIT_KEY,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": "5000",
        }
        
        r = requests.get(
            BYBIT_URL + "/v5/account/info",
            headers=headers,
            timeout=5
        )
        
        if r.status_code == 200:
            response = r.json()
            if response.get("retCode") == 0:
                print("✅ Bybit Demo API keys are valid")
                
                params = {
                    "category": "linear",
                    "symbol": symbol,
                    "buyLeverage": str(lev),
                    "sellLeverage": str(lev)
                }
                
                signature = bybit_sign({}, timestamp, json.dumps(params))
                headers["X-BAPI-SIGN"] = signature
                headers["Content-Type"] = "application/json"
                
                r = requests.post(
                    BYBIT_URL + "/v5/position/set-leverage",
                    headers=headers,
                    json=params,
                    timeout=5
                )
                print(f"Bybit leverage response: {r.status_code} - {r.text}")
            else:
                print(f"❌ Bybit API error: {response.get('retMsg', 'Unknown error')}")
                print("⚠️ Get new Demo API keys from: https://www.bybit.com (Demo Trading)")
        else:
            print(f"❌ Bybit API connection failed: {r.status_code}")
            
        return {}
    except Exception as e:
        print(f"Bybit leverage error: {e}")
        return {}

def get_bybit_symbol_filters(symbol):
    """Fetch Bybit instrument info for qty step and tick size"""
    try:
        url = BYBIT_URL + f"/v5/market/instruments-info?category=linear&symbol={symbol}"
        r = requests.get(url, timeout=3)
        data = r.json()
        
        filters = {"step_size": "1", "tick_size": "0.01"}
        if data.get("retCode") == 0:
            result = data.get("result", {}).get("list", [])
            if result:
                filters["step_size"] = result[0].get("lotSizeFilter", {}).get("qtyStep", "1")
                filters["tick_size"] = result[0].get("priceFilter", {}).get("tickSize", "0.01")
                return filters
        return filters
    except Exception as e:
        print(f"⚠️ CRITICAL: Failed to fetch Bybit filters: {e}")
        print(f"⚠️ Cannot continue without symbol info. Please check API connection.")
        return None  # ✅ Return None to signal failure

def bybit_limit_order(symbol, side, qty, price, step_size, tick_size):
    for attempt in range(3):
        try:
            qty = round_step_size(qty, step_size)
            price = round_price(price, tick_size)
            timestamp = str(int(get_accurate_time() * 1000))
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": "Limit",
                "qty": str(qty),
                "price": str(price),
                "timeInForce": "PostOnly"
            }
            signature = bybit_sign({}, timestamp, json.dumps(params))
            headers = {"X-BAPI-API-KEY": BYBIT_KEY, "X-BAPI-TIMESTAMP": timestamp, "X-BAPI-SIGN": signature, "X-BAPI-RECV-WINDOW": "5000", "Content-Type": "application/json"}
            audit_log(f"Bybit Limit Req: {side} {qty} @ {price} (Post-Only) | Attempt {attempt+1}")
            r = requests.post(BYBIT_URL + "/v5/order/create", headers=headers, json=params, timeout=5)
            res = r.json()
            
            # Bybit transient codes: 10002 (Expired), 10006 (Rate limit), 10016 (System error)
            if res.get("retCode") in [10002, 10006, 10016]:
                audit_log(f"⚠️ Bybit transient error {res['retCode']}: {res.get('retMsg')}. Retrying...")
                time.sleep(1)
                continue

            audit_log(f"Bybit Limit Res: {json.dumps(res)}")
            return res
        except Exception as e:
            audit_log(f"💥 Bybit limit order exception (Attempt {attempt+1}): {e}")
            if attempt < 2: time.sleep(1)
    return {}

def bybit_cancel_order(symbol, order_id):
    try:
        timestamp = str(int(get_accurate_time() * 1000))
        params = {"category": "linear", "symbol": symbol, "orderId": order_id}
        signature = bybit_sign({}, timestamp, json.dumps(params))
        headers = {"X-BAPI-API-KEY": BYBIT_KEY, "X-BAPI-TIMESTAMP": timestamp, "X-BAPI-SIGN": signature, "X-BAPI-RECV-WINDOW": "5000", "Content-Type": "application/json"}
        r = requests.post(BYBIT_URL + "/v5/order/cancel", headers=headers, json=params, timeout=5)
        return r.json()
    except Exception as e:
        print(f"Bybit cancel error: {e}")
        return {}

def bybit_get_order(symbol, order_id):
    try:
        timestamp = str(int(get_accurate_time() * 1000))
        params = {"category": "linear", "symbol": symbol, "orderId": order_id}
        signature = bybit_sign(params, timestamp, "")
        
        # Manual construction to ensure signature match
        queryString = urlencode(sorted(params.items()))
        url = f"{BYBIT_URL}/v5/order/realtime?{queryString}"
        
        headers = {
            "X-BAPI-API-KEY": BYBIT_KEY, 
            "X-BAPI-TIMESTAMP": timestamp, 
            "X-BAPI-SIGN": signature, 
            "X-BAPI-RECV-WINDOW": "5000"
        }
        
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200:
            print(f"Bybit order fetch error: {r.status_code} - {r.text}")
            return {}
            
        return r.json()
    except Exception as e:
        print(f"Bybit get order error: {e}")
        return {}

def bybit_order(symbol, side, qty, step_size):
    for attempt in range(3):
        try:
            qty = round_step_size(qty, step_size)
            timestamp = str(int(get_accurate_time() * 1000))
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": "Market",
                "qty": str(qty),
                "timeInForce": "IOC"
            }
            signature = bybit_sign({}, timestamp, json.dumps(params))
            headers = {"X-BAPI-API-KEY": BYBIT_KEY, "X-BAPI-TIMESTAMP": timestamp, "X-BAPI-SIGN": signature, "X-BAPI-RECV-WINDOW": "5000", "Content-Type": "application/json"}
            r = requests.post(BYBIT_URL + "/v5/order/create", headers=headers, json=params, timeout=5)
            res = r.json()
            
            if res.get("retCode") in [10002, 10006, 10016]:
                audit_log(f"⚠️ Bybit Market transient error {res['retCode']}: {res.get('retMsg')}. Retrying...")
                time.sleep(1)
                continue
                
            return res
        except Exception as e:
            print(f"Bybit order error (Attempt {attempt+1}): {e}")
            if attempt < 2: time.sleep(1)
    return {}

async def limit_order_chaser(exchange, symbol, side, total_qty, state, step_size, tick_size, trade_records):
    audit_log(f"🏁 ULTRA-AGGRESSIVE CHASER START: {exchange.upper()} | {side} {total_qty}")
    remaining_qty = total_qty
    active_order_id = None
    iteration = 0
    total_filled = 0.0
    filled_baseline = 0.0  # ✅ Track fills before current order
    last_price = None  # ✅ Track last order price
    
    float_step = float(step_size)
    
    while remaining_qty >= float_step:
        iteration += 1
        
        # ✅ Get current BBO (bid/ask, NOT mark price)
        if side.upper() in ["BUY", "LONG", "Buy"]:
            target_price = state[exchange]["bid"]  # Join the best bid
        else:
            target_price = state[exchange]["ask"]  # Join the best ask
        
        if active_order_id:
            # ✅ Fetch order status
            status = None
            if exchange == "binance":
                res = binance_get_order(symbol, active_order_id)
                if res and "orderId" in res:
                    status = {
                        "filled": float(res.get("executedQty", 0)),
                        "price": float(res.get("price", 0)),
                        "status": res.get("status", "UNKNOWN")
                    }
            else:  # bybit
                res = bybit_get_order(symbol, active_order_id)
                result_list = res.get("result", {}).get("list", [])
                if result_list:
                    o = result_list[0]
                    status = {
                        "filled": float(o.get("cumExecQty", 0)),
                        "price": float(o.get("price", 0)),
                        "status": o.get("status", "Unknown")
                    }
            
            if not status:
                audit_log(f"⚠️ Failed to fetch order status, retrying...")
                await asyncio.sleep(0.05)
                continue
            
            # Update fills
            current_delta = float(status["filled"])
            total_filled = filled_baseline + current_delta
            remaining_qty = total_qty - total_filled
            
            audit_log(f"{exchange.upper()} 🔍 Iter#{iteration}: Filled {total_filled}/{total_qty} | "
                     f"Order@{status['price']:.4f} | Target@{target_price:.4f}")
            
            # ✅ Check if fully filled
            if remaining_qty <= 0.001 or status["status"] in ["FILLED", "Filled"]:
                audit_log(f"🎯 {exchange.upper()} FULLY FILLED!")
                break
            
            # ✅ Handle terminal states
            terminal_states = {
                "binance": ["REJECTED", "EXPIRED", "EXPIRED_IN_MATCH"],
                "bybit": ["Rejected", "Cancelled", "PartiallyFilledCanceled", "Deactivated"]
            }
            
            if status["status"] in terminal_states.get(exchange, []):
                audit_log(f"{exchange.upper()} ⚠️ Terminal state: {status['status']}. Placing new order...")
                active_order_id = None
                last_price = None
                continue
            
            # ✅ ULTRA-AGGRESSIVE: Cancel if price moves by more than 1 tick
            if abs(status["price"] - target_price) >= float(tick_size):
                audit_log(f"{exchange.upper()} 🔄 PRICE MOVED >= TICK! {status['price']:.4f} → {target_price:.4f} | CANCELING!")
                
                # Cancel order
                if exchange == "binance":
                    binance_cancel_order(symbol, active_order_id)
                else:
                    bybit_cancel_order(symbol, active_order_id)
                
                await asyncio.sleep(0.1)  # Brief wait for cancel confirmation
                
                # Re-fetch final fills
                final_filled = 0.0
                if exchange == "binance":
                    res = binance_get_order(symbol, active_order_id)
                    if res and "orderId" in res:
                        final_filled = float(res.get("executedQty", 0))
                else:
                    res = bybit_get_order(symbol, active_order_id)
                    result_list = res.get("result", {}).get("list", [])
                    if result_list:
                        final_filled = float(result_list[0].get("cumExecQty", 0))
                
                total_filled = filled_baseline + float(final_filled)
                remaining_qty = total_qty - total_filled
                
                audit_log(f"{exchange.upper()} 📉 Post-cancel: Filled={total_filled}, Remaining={remaining_qty}")
                
                if remaining_qty <= 0.001:
                    audit_log(f"{exchange.upper()} 🎯 Filled during cancel!")
                    break
                
                active_order_id = None
                last_price = None
                continue
            
            # ✅ ULTRA-FAST: Check every 20ms (50 times per second!)
            await asyncio.sleep(0.02)
            continue
        
        # ✅ Place new order if none active
        if not active_order_id and remaining_qty >= float_step:
            qty_to_order = round_step_size(remaining_qty, step_size)
            
            if qty_to_order <= 0:
                audit_log(f"{exchange.upper()} 🧹 Dust remaining ({remaining_qty}), finishing.")
                break
            
            audit_log(f"{exchange.upper()} 🆕 Placing {side} @ {target_price:.4f} for {qty_to_order}")
            
            res = {}
            if exchange == "binance":
                res = binance_limit_order(symbol, side, qty_to_order, target_price, step_size, tick_size)
                active_order_id = res.get("orderId")
            else:
                order_side = "Buy" if side.upper() in ["BUY", "LONG"] else "Sell"
                res = bybit_limit_order(symbol, order_side, qty_to_order, target_price, step_size, tick_size)
                active_order_id = res.get("result", {}).get("orderId")
            
            if active_order_id:
                trade_records[exchange]["entry_order_ids"].append(active_order_id)

            if not active_order_id:
                audit_log(f"{exchange.upper()} ⚠️ Order rejected: {json.dumps(res)}")
                await asyncio.sleep(0.2)
                continue
            
            last_price = target_price  # Track this order's price
            filled_baseline = total_filled # ✅ Store fills BEFORE this order
            audit_log(f"{exchange.upper()} ✅ Order placed: {active_order_id}")
        
        await asyncio.sleep(0.02)  # ✅ ULTRA-FAST loop (50 checks/sec)
    
    audit_log(f"{exchange.upper()} 🏁 CHASER FINISHED: {total_filled}/{total_qty} filled")

    # =========================
    # BYBIT PNL FETCHER (NEW)
    # =========================
async def api_pnl_tracker(state, coin, exchanges, pos_info):
    """Calculate PNL manually using mark price, refreshing position info every 5s"""
    binance_symbol = coin + "USDT"
    bybit_symbol = coin + "USDT"
    
    await asyncio.sleep(1)  # Wait 1 sec after trade execution
    audit_log("💰 Starting Async PNL tracker...")
    
    iteration = 0
    async with aiohttp.ClientSession(headers={"X-MBX-APIKEY": BINANCE_KEY}) as session:
        while state.get("running", True):
            try:
                is_exiting = state.get("exit_triggered", False)
                sync_now = True if is_exiting else (iteration % 10 == 0)

                if sync_now:
                    tasks = []
                    if "binance" in exchanges:
                        tasks.append(get_binance_entry_info(session, binance_symbol))
                    if "bybit" in exchanges:
                        tasks.append(get_bybit_entry_info(session, bybit_symbol))
                    
                    results = await asyncio.gather(*tasks)
                    
                    # Update results based on return order
                    idx = 0
                    if "binance" in exchanges:
                        if results[idx]: pos_info["binance"] = results[idx]
                        idx += 1
                    if "bybit" in exchanges:
                        if results[idx]: pos_info["bybit"] = results[idx]
            
                net_pnl = 0.0
                # Binance PNL (Taker Exit)
                b_info = pos_info.get("binance")
                if b_info and b_info.get("entry_price"):
                    entry = b_info["entry_price"]
                    size = b_info["size"]
                    # Taker exit: Use BID for LONG, ASK for SHORT
                    exit_p = state["binance"]["bid"] if b_info["side"] == "LONG" else state["binance"]["ask"]
                    if exit_p > 0:
                        pnl = (exit_p - entry) * size if b_info["side"] == "LONG" else (entry - exit_p) * size
                        state["binance"]["pnl"] = pnl
                        net_pnl += pnl
                
                # Bybit PNL (Taker Exit)
                y_info = pos_info.get("bybit")
                if y_info and y_info.get("entry_price"):
                    entry = y_info["entry_price"]
                    size = y_info["size"]
                    # Taker exit: Use BID for Buy, ASK for Sell
                    exit_p = state["bybit"]["bid"] if y_info["side"] == "Buy" else state["bybit"]["ask"]
                    if exit_p > 0:
                        pnl = (exit_p - entry) * size if y_info["side"] == "Buy" else (entry - exit_p) * size
                        state["bybit"]["pnl"] = pnl
                        net_pnl += pnl
                
                state["net_pnl"] = net_pnl
                iteration += 1
                await asyncio.sleep(0.2)
                
            except Exception as e:
                # audit_log(f"PNL calculation error: {e}")
                await asyncio.sleep(1)

def calculate_exit_pnl_projection(position_info, state):
    """Calculate projected PNL if we close ALL remaining positions at current BBO"""
    net_projection = 0.0
    
    # Binance
    if position_info.get("binance") and position_info["binance"].get("entry_price"):
        entry = position_info["binance"]["entry_price"]
        size = position_info["binance"]["size"]
        side = position_info["binance"]["side"]
        
        # Use BID for LONG exit, ASK for SHORT exit
        exit_price = state["binance"]["bid"] if side == "LONG" else state["binance"]["ask"]
        
        if exit_price <= 0: return None  # Data not ready
        
        if side == "LONG":
            projected_pnl = (exit_price - entry) * size
        else:
            projected_pnl = (entry - exit_price) * size
        
        net_projection += projected_pnl
    
    # Bybit
    if position_info.get("bybit") and position_info["bybit"].get("entry_price"):
        entry = position_info["bybit"]["entry_price"]
        size = position_info["bybit"]["size"]
        side = position_info["bybit"]["side"]
        
        # Use BID for Buy exit, ASK for Sell exit
        exit_price = state["bybit"]["bid"] if side == "Buy" else state["bybit"]["ask"]
        
        if exit_price <= 0: return None  # Data not ready
        
        if side == "Buy":
            projected_pnl = (exit_price - entry) * size
        else:
            projected_pnl = (entry - exit_price) * size
        
        net_projection += projected_pnl
    
    return net_projection

def time_left_precise(ts):
    """Return seconds until funding (for debugging)"""
    if not ts:
        return "N/A"
    diff = int(ts / 1000 - get_accurate_time())  # Use NTP-synced time
    return f"{diff}s"
    
# =========================
# PRINTER (UPDATED)
# =========================
async def printer(state, exchanges):
    while state.get("running", True):
        print("\n" + "=" * 90)
        # 1. Exchange Data
        for ex in exchanges:
            price_str = f"{state[ex]['price']:.6f}" if state[ex]['price'] else "N/A"
            funding_str = f"{state[ex]['funding']:.4f}%" if state[ex]['funding'] is not None else "N/A"
            time_str = time_left(state[ex]['next_ts'])
            
            pnl = state[ex].get("pnl", None)
            if pnl is not None:
                pnl_str = f"${pnl:+.3f}"
                color = "\033[92m" if pnl >= 0 else "\033[91m"
                reset = "\033[0m"
                pnl_display = f"{color}{pnl_str}{reset}"
            else:
                pnl_display = "Waiting..."
            
            print(f"{ex.upper():7} | Price: {price_str} | Funding: {funding_str} | "
                  f"Time: {time_str} | PNL: {pnl_display}")
            
        # 2. Strategy & Signal Status
        print("-" * 90)
        if not state.get("trade_fired"):
            sig = state.get("signal")
            if sig:
                print(f"📡 SIGNAL ACTIVE: LONG {sig['long'].upper()} / SHORT {sig['short'].upper()}")
                print(f"   Spread: {sig['spread']:.4f}% | Target Req: {state.get('min_spread')}%")
            else:
                print(f"📡 SEARCHING: Scanning for arbitrage spread > {state.get('min_spread')}%...")
            
            print(f"🕒 TRIGGERS AT: {state.get('execution_time')} before funding")
        else:
            print(f"🚀 POSITION ACTIVE | Strategy: {state.get('active_strategy', 'Hedged')}")
            exit_info = state.get('exit_time') if state.get('exit_mode') == "2" else "Funding Reset (00:00:00)"
            print(f"🕒 EXIT TARGET: {exit_info}")

        # 3. Footer & Net PNL
        adjust_info = f" (Adj: {MANUAL_ADJUST:+d}s)" if MANUAL_ADJUST != 0 else ""
        if adjust_info:
             print(f"Note: Manual Time Adjustment Active{adjust_info}")
        
        net_pnl = state.get("net_pnl", None)
        if net_pnl is not None:
            net_color = "\033[92m\033[1m" if net_pnl >= 0 else "\033[91m\033[1m"
            reset = "\033[0m"
            print("=" * 90)
            print(f"💰 NET PNL: {net_color}${net_pnl:+.3f}{reset}")
            
            # 🆕 INTEGRATED PROJECTION (Cleaner terminal)
            proj_pnl = state.get("exit_pnl_projection")
            if proj_pnl is not None:
                proj_color = "\033[92m" if proj_pnl >= 0 else "\033[91m"
                print(f"⏳ Waiting for positive PNL... Current: {proj_color}${proj_pnl:+.3f}{reset}")
        
        await asyncio.sleep(0.2)

# =========================
# TIME CHECKER
# =========================
def should_execute(ts, target_time_str):
    """Check if current time matches target execution time"""
    if not ts:
        return False
    
    # Calculate seconds until funding
    ts_seconds = ts / 1000
    current_time = get_accurate_time()  # Use NTP-synced time
    seconds_until_funding = int(ts_seconds - current_time)
    
    if seconds_until_funding <= 0:
        print(f"⚠️ Funding time already passed! (diff: {seconds_until_funding}s)")
        return False  # Funding already passed
    
    # Parse target time string (HH:MM:SS)
    try:
        target_h, target_m, target_s = map(int, target_time_str.split(':'))
        target_seconds = target_h * 3600 + target_m * 60 + target_s
        
        # ✅ FIX: Trigger EXACTLY at target time (±1 second tolerance)
        return abs(target_seconds - seconds_until_funding) <= 1
        
    except Exception as e:
        print(f"❌ Error parsing target time '{target_time_str}': {e}")
        return False
async def fetch_binance_trades_by_orders(session, symbol, order_ids):
    """Fetch all fills for given Binance order IDs"""
    try:
        if not order_ids: return []
        params = binance_sign({
            "symbol": symbol,
            "limit": 100,
            "timestamp": int(get_accurate_time() * 1000)
        })
        async with session.get(BINANCE_URL + "/fapi/v1/userTrades", params=params, timeout=5) as r:
            trades = await r.json()
            if isinstance(trades, list):
                return [t for t in trades if str(t.get("orderId")) in [str(o) for o in order_ids]]
        return []
    except Exception as e:
        audit_log(f"Binance trade fetch error: {e}")
        return []

async def fetch_bybit_trades_by_orders(session, symbol, order_ids):
    """Fetch all fills for given Bybit order IDs"""
    try:
        if not order_ids: return []
        timestamp = str(int(get_accurate_time() * 1000))
        params = {"category": "linear", "symbol": symbol, "limit": "100"}
        signature = bybit_sign(params, timestamp, "")
        queryString = urlencode(sorted(params.items()))
        url = f"{BYBIT_URL}/v5/execution/list?{queryString}"
        headers = {"X-BAPI-API-KEY": BYBIT_KEY, "X-BAPI-TIMESTAMP": timestamp, "X-BAPI-SIGN": signature, "X-BAPI-RECV-WINDOW": "5000"}
        async with session.get(url, headers=headers, timeout=5) as r:
            data = await r.json()
            if data.get("retCode") == 0:
                trades = data.get("result", {}).get("list", [])
                return [t for t in trades if str(t.get("orderId")) in [str(o) for o in order_ids]]
        return []
    except Exception as e:
        audit_log(f"Bybit trade fetch error: {e}")
        return []

async def generate_final_report(trade_records, coin):
    """Generate and display final trade report with retries for late data"""
    audit_log("\n" + "="*40 + " FINAL TRADE REPORT " + "="*40)
    total_fee = 0.0
    total_realized_pnl = 0.0
    
    # Wait 3 seconds instead of 1 for exchange sync
    await asyncio.sleep(3)
    
    async with aiohttp.ClientSession(headers={"X-MBX-APIKEY": BINANCE_KEY}) as session:
        for ex in ["binance", "bybit"]:
            symbol = coin + "USDT"
            
            # Retry mechanism for Bybit/Binance lag
            for attempt in range(100):
                if ex == "binance":
                    entry_trades = await fetch_binance_trades_by_orders(session, symbol, trade_records[ex]["entry_order_ids"])
                    exit_trades = await fetch_binance_trades_by_orders(session, symbol, trade_records[ex]["exit_order_ids"])
                else:
                    entry_trades = await fetch_bybit_trades_by_orders(session, symbol, trade_records[ex]["entry_order_ids"])
                    exit_trades = await fetch_bybit_trades_by_orders(session, symbol, trade_records[ex]["exit_order_ids"])
                
                # If we expect data but got none, wait and retry
                if (trade_records[ex]["entry_order_ids"] and not entry_trades) or \
                   (trade_records[ex]["exit_order_ids"] and not exit_trades):
                    await asyncio.sleep(2)
                    continue
                break

            def process_trades(trades, exchange):
                total_qty = sum(float(t.get("qty") or t.get("execQty", 0)) for t in trades)
                total_val = sum(float(t.get("quoteQty") or (float(t.get("execQty", 0)) * float(t.get("execPrice", 0)))) for t in trades)
                fees = sum(float(t.get("commission") or t.get("execFee", 0)) for t in trades)
                asset = trades[0].get("commissionAsset") if (trades and exchange == "binance") else ("USDT" if trades else "")
                avg_price = total_val / total_qty if total_qty > 0 else 0
                return total_qty, avg_price, fees, asset

            ent_qty, ent_p, ent_f, ent_a = process_trades(entry_trades, ex)
            ext_qty, ext_p, ext_f, ext_a = process_trades(exit_trades, ex)
            
            # Calculate REALIZED PNL for this side
            side = trade_records[ex]['side']
            if side in ["LONG", "Buy"]:
                realized_pnl = (ext_p - ent_p) * min(ent_qty, ext_qty) - (ent_f + ext_f)
            else: # SHORT or Sell
                realized_pnl = (ent_p - ext_p) * min(ent_qty, ext_qty) - (ent_f + ext_f)
            
            total_fee += (ent_f + ext_f)
            total_realized_pnl += realized_pnl
            
            audit_log(f"[{ex.upper()}] Side: {side}")
            audit_log(f"  Entry: {ent_qty} @ ${ent_p:.6f} | Total: ${ent_qty*ent_p:.2f} | Fee: ${ent_f:.6f} {ent_a}")
            audit_log(f"  Exit:  {ext_qty} @ ${ext_p:.6f} | Total: ${ext_qty*ext_p:.2f} | Fee: ${ext_f:.6f} {ext_a}")
            audit_log(f"  REALIZED PNL: ${realized_pnl:+.4f} USDT")
        
    audit_log(f"\n� --- SUMMARY ---")
    audit_log(f"💰 TOTAL FEES: ${total_fee:.6f} USDT")
    audit_log(f"💰 COMBINED REALIZED PNL: {total_realized_pnl:+.4f} USDT")
    audit_log("="*100 + "\n")

# =========================
# MAIN
# =========================
async def main():
    # Sync time with NTP servers first
    print("🕐 Syncing time with NTP servers...")
    sync_time_with_ntp()
    print()
    
    coin = input("Coin (BTC/ETH/SOL): ").upper()
    exchanges = input("Exchanges (binance,bybit,mexc): ").lower().split(",")
    usdt = float(input("USDT per side: "))
    leverage = int(input("Leverage: "))
    EXECUTION_TIME = input("Execute at funding time left (HH:MM:SS): ")
    print("\nExit Options:")
    print("1. Auto-exit when funding resets (00:00:00)")
    print("2. Exit at custom time before funding")
    exit_mode = input("Choose exit mode (1/2): ").strip()

    if exit_mode == "1":
        EXIT_TIME = None
        print("✅ Will auto-exit when funding resets!")
    elif exit_mode == "2":
        EXIT_TIME = input("Exit at funding time left (HH:MM:SS): ")
        print(f"✅ Will exit at {EXIT_TIME} before funding!")
    else:
        print("Invalid choice, defaulting to auto-exit")
        EXIT_TIME = None
        exit_mode = "1"
    
    MIN_SPREAD = float(input("Minimum funding spread (%): "))
    
    # Sync with specific exchange for better accuracy
    print("\n🕐 Re-syncing with exchange time for precision...")
    if "binance" in exchanges:
        get_binance_server_time()
    elif "bybit" in exchanges:
        get_bybit_server_time()

    state = {
        "running": True,
        "net_pnl": None,
        "signal": None,
        "trade_fired": False,
        "min_spread": MIN_SPREAD,
        "execution_time": EXECUTION_TIME,
        "exit_mode": exit_mode,
        "exit_time": EXIT_TIME if exit_mode == "2" else "Funding Reset (+5s)",
        "exit_triggered": False
    }
    position_info = {
        "binance": {"entry_price": None, "size": 0, "side": None},
        "bybit": {"entry_price": None, "size": 0, "side": None}
    }
    trade_records = {
        "binance": {"entry_order_ids": [], "exit_order_ids": [], "side": None},
        "bybit": {"entry_order_ids": [], "exit_order_ids": [], "side": None}
    }
    tasks = []

    if "binance" in exchanges:
        state["binance"] = {"price": 0, "bid": 0, "ask": 0, "funding": None, "next_ts": None, "pnl": None}
        tasks.append(binance_ws(coin + "USDT", state))
    if "bybit" in exchanges:
        state["bybit"] = {"price": 0, "bid": 0, "ask": 0, "funding": None, "next_ts": None, "pnl": None}
        tasks.append(bybit_ws(coin + "USDT", state))
    if "mexc" in exchanges:
        state["mexc"] = {"price": 0, "bid": 0, "ask": 0, "funding": None, "next_ts": None, "pnl": None}
        tasks.append(mexc_rest(coin + "_USDT", state))

    trade_fired = False
    exit_fired = False

    async def execution_watcher(position_info):
        nonlocal trade_fired
        nonlocal trade_records  # Add this line
        print(f"\n⏰ Waiting for execution time: {EXECUTION_TIME} before funding")
        print("📊 Monitoring funding rates...")
        
        binance_symbol = coin + "USDT"
        bybit_symbol = coin + "USDT"
        binance_step = get_binance_symbol_filters(binance_symbol)
        bybit_step = get_bybit_symbol_filters(bybit_symbol)
        
        # ✅ Validate filters
        if not binance_step or not bybit_step:
            print("❌ CRITICAL ERROR: Failed to fetch symbol filters!")
            print("   Cannot place orders without proper step size and tick size.")
            print("   Please check API connectivity and try again.")
            return  # Exit function safely

        print(f"📏 Binance stepSize: {binance_step}, Bybit qtyStep: {bybit_step}")
        
        while state.get("running", True):
            if "binance" in exchanges and "bybit" in exchanges:
                if (state["binance"]["next_ts"] and state["bybit"]["next_ts"] and
                    not trade_fired):
                    
                    sig = funding_arbitrage_signal(state, exchanges, MIN_SPREAD)
                    state["signal"] = sig
                    
                    exchange_to_check = "binance" if "binance" in exchanges else "bybit"
                    
                    if should_execute(state[exchange_to_check]["next_ts"], EXECUTION_TIME):
                        if sig and sig['spread'] >= MIN_SPREAD:
                            audit_log(f"🚀 EXECUTING HEDGE at {time_left(state[exchange_to_check]['next_ts'])}")
                            audit_log(f"Strategy: Long {sig['long']}, Short {sig['short']}")
                            
                            binance_set_leverage(binance_symbol, leverage)
                            bybit_set_leverage(bybit_symbol, leverage)
                            
                            # ✅ TRUE USDT-NEUTRAL HEDGE
                            target_usdt = usdt * leverage
                            
                            # 1. Calculate Binance independently
                            qty_b_ideal = target_usdt / state["binance"]["price"]
                            pure_qty_b = round_step_size_nearest(qty_b_ideal, binance_step["step_size"])
                            actual_usdt_b = pure_qty_b * state["binance"]["price"]
                            
                            # 2. Calculate Bybit independently
                            qty_y_ideal = target_usdt / state["bybit"]["price"]
                            pure_qty_y = round_step_size(qty_y_ideal, bybit_step["step_size"])
                            actual_usdt_y = pure_qty_y * state["bybit"]["price"]
                            
                            mismatch = actual_usdt_b - actual_usdt_y
                            
                            audit_log(f"📐 USDT-Neutral Search: Target=${target_usdt:.2f}")
                            audit_log(f"🎯 Binance: {pure_qty_b} coins (~${actual_usdt_b:.4f})")
                            audit_log(f"🎯 Bybit:   {pure_qty_y} coins (~${actual_usdt_y:.4f})")
                            audit_log(f"⚖️ Parity Delta: ${abs(mismatch):.6f}")
                            
                            if pure_qty_b <= 0 or pure_qty_y <= 0:
                                print("❌ Error: Calculated quantity is 0. Increase USDT or Leverage.")
                                return

                            # Use Limit Order Chasing
                            # ... (task execution remains same) ...
                            tasks_chaser = []
                            if sig["long"] == "binance":
                                tasks_chaser.append(limit_order_chaser("binance", binance_symbol, "BUY", pure_qty_b, state, binance_step["step_size"], binance_step["tick_size"], trade_records))
                            else:
                                tasks_chaser.append(limit_order_chaser("binance", binance_symbol, "SELL", pure_qty_b, state, binance_step["step_size"], binance_step["tick_size"], trade_records))
                            
                            if sig["long"] == "bybit":
                                tasks_chaser.append(limit_order_chaser("bybit", bybit_symbol, "Buy", pure_qty_y, state, bybit_step["step_size"], bybit_step["tick_size"], trade_records))
                            else:
                                tasks_chaser.append(limit_order_chaser("bybit", bybit_symbol, "Sell", pure_qty_y, state, bybit_step["step_size"], bybit_step["tick_size"], trade_records))
                            
                            # Wait for both and log parity
                            await asyncio.gather(*tasks_chaser)
                            audit_log(f"SYSTEM ⚖️ HEDGE PARITY AUDIT: Delta=${abs(mismatch):.6f}")
                            
                            # Store position sides
                            trade_records["binance"]["side"] = "LONG" if sig["long"] == "binance" else "SHORT"
                            trade_records["bybit"]["side"] = "Buy" if sig["long"] == "bybit" else "Sell"
                            
                            trade_fired = True
                            state["trade_fired"] = True
                            state["active_strategy"] = f"Long {sig['long']} / Short {sig['short']}"
                            # 🆕 CAPTURE funding time when trade executes
                            nonlocal funding_time_snapshot
                            funding_time_snapshot = state[exchange_to_check]["next_ts"]
                            print("✅ Orders placed! Fetching position info...")
                            
                            # Wait 500ms for orders to settle
                            await asyncio.sleep(0.5)

                            # Fetch entry prices and sizes with retry
                            if "binance" in exchanges:
                                async with aiohttp.ClientSession(headers={"X-MBX-APIKEY": BINANCE_KEY}) as session:
                                    for attempt in range(10):
                                        binance_info = await get_binance_entry_info(session, binance_symbol)
                                        if binance_info:
                                            position_info["binance"] = binance_info
                                            print(f"✅ Binance: Entry=${binance_info['entry_price']:.2f}, Size={binance_info['size']}, Side={binance_info['side']}")
                                            break
                                        print(f"⏳ Waiting for Binance position... (attempt {attempt + 1}/10)")
                                        await asyncio.sleep(0.2)
                            
                            if "bybit" in exchanges:
                                async with aiohttp.ClientSession() as session:
                                    for attempt in range(10):
                                        bybit_info = await get_bybit_entry_info(session, bybit_symbol)
                                        if bybit_info:
                                            position_info["bybit"] = bybit_info
                                            print(f"✅ Bybit: Entry=${bybit_info['entry_price']:.2f}, Size={bybit_info['size']}, Side={bybit_info['side']}")
                                            break
                                        print(f"⏳ Waiting for Bybit position... (attempt {attempt + 1}/10)")
                                        await asyncio.sleep(0.2)

                            # Debug: Check if position info was fetched
                            if not position_info["binance"]["entry_price"] and "binance" in exchanges:
                                print("⚠️ WARNING: Binance position info not found!")
                            if not position_info["bybit"]["entry_price"] and "bybit" in exchanges:
                                print("⚠️ WARNING: Bybit position info not found!")

                            # Start API-based PNL tracker using the shared position_info
                            print("💰 Starting API-based PNL tracking...")
                            asyncio.create_task(api_pnl_tracker(state, coin, exchanges, position_info))
                            
                        else:
                            print(f"❌ No valid signal (spread: {sig['spread'] if sig else 'N/A'}%, "
                                  f"min required: {MIN_SPREAD}%)")
            
            await asyncio.sleep(0.05)

    funding_time_snapshot = None

    async def exit_watcher():
        nonlocal exit_fired, exit_mode, funding_time_snapshot
        nonlocal trade_records  # Add this line
        
        if exit_mode == "1":
            print(f"\n⏰ Exit will trigger automatically when funding resets (00:00:00)")
        else:
            print(f"\n⏰ Exit will trigger at: {EXIT_TIME} before funding")   
                
        binance_symbol = coin + "USDT"
        bybit_symbol = coin + "USDT"
        binance_step = get_binance_symbol_filters(binance_symbol)
        bybit_step = get_bybit_symbol_filters(bybit_symbol)
        
        while not trade_fired:
            await asyncio.sleep(1)  # Wait until trade is executed
        
        print("✅ Trade executed, monitoring for exit time...")
        
        while not exit_fired:
            exchange_to_check = "binance" if "binance" in exchanges else "bybit"
            
            # Check exit condition based on mode
            should_exit = False
    
            if exit_mode == "1":
                # Auto-exit when funding resets (using CAPTURED time)
                if funding_time_snapshot:
                    ts_seconds = funding_time_snapshot / 1000
                    current_time = get_accurate_time()
                    seconds_until_funding = int(ts_seconds - current_time)

                    if seconds_until_funding <= -5:   # Exit 5 seconds AFTER funding reset
                        should_exit = True
            else:
                # Custom time exit - Use CAPTURED time to avoid issues when live next_ts updates
                if funding_time_snapshot:
                    should_exit = should_execute(funding_time_snapshot, EXIT_TIME)
    
            if should_exit:
                print(f"\n🚪 EXIT TIME REACHED! Now waiting for positive PNL...")
                state["exit_triggered"] = True  # 🚀 TRIGGER ULTRA-HIGH FREQUENCY SYNC
    
                # 🆕 NEW FEATURE: Wait for positive PNL before exiting (REAL-TIME)
                while True:
                    # ✅ Calculate PNL in REAL-TIME using live BBO prices
                    projected_pnl = calculate_exit_pnl_projection(position_info, state)
                    state["exit_pnl_projection"] = projected_pnl # Update for printer
                    
                    if projected_pnl is None:
                        await asyncio.sleep(0.01)
                        continue

                    if projected_pnl >= 0:
                        audit_log(f"✅ PNL is positive (${projected_pnl:+.3f})! Closing now...")
                        break
                    
                    await asyncio.sleep(0.001)  # Check every 1ms with LIVE data (BG ONLY)
    
                print(f"\n🚪 CLOSING ALL POSITIONS...")
                
                # Close Binance position
                if "binance" in exchanges and position_info["binance"]["entry_price"]:
                    side_to_close = "SELL" if position_info["binance"]["side"] == "LONG" else "BUY"
                    qty = position_info["binance"]["size"]
                    print(f"Closing Binance {position_info['binance']['side']} with {side_to_close} order...")
                    res = binance_order(binance_symbol, side_to_close, qty, binance_step["step_size"])
                    if res.get("orderId"):
                        trade_records["binance"]["exit_order_ids"].append(res.get("orderId"))
                
                # Close Bybit position
                if "bybit" in exchanges and position_info["bybit"]["entry_price"]:
                    side_to_close = "Sell" if position_info["bybit"]["side"] == "Buy" else "Buy"
                    qty = position_info["bybit"]["size"]
                    print(f"Closing Bybit {position_info['bybit']['side']} with {side_to_close} order...")
                    res = bybit_order(bybit_symbol, side_to_close, qty, bybit_step["step_size"])
                    if res.get("result", {}).get("orderId"):
                        trade_records["bybit"]["exit_order_ids"].append(res.get("result", {}).get("orderId"))
                
                exit_fired = True
                audit_log("✅ All positions closed!")
                
                # SHUTDOWN Background Tasks
                state["running"] = False
                audit_log("🛑 Stopping background processes...")
                await asyncio.sleep(1) # Wait for loops to see flag

                # Generate final report
                print("\n" + "="*90)
                print("📊 Fetching exact trade data from exchanges...")
                await generate_final_report(trade_records, coin)
                break
            
            await asyncio.sleep(0.05)
    tasks.append(printer(state, exchanges))
    tasks.append(execution_watcher(position_info))
    tasks.append(exit_watcher())
    await asyncio.gather(*tasks)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    asyncio.run(main())