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

# =========================
# BINANCE WS (MARK + FUNDING)
# =========================
async def binance_ws(symbol, state):
    url = f"wss://fstream.binance.com/ws/{symbol.lower()}@markPrice"
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                print("✅ Binance WS connected")
                async for msg in ws:
                    d = json.loads(msg)
                    state["binance"]["price"] = float(d["p"])
                    state["binance"]["funding"] = float(d["r"]) * 100
                    state["binance"]["next_ts"] = int(d["T"])
        except Exception as e:
            print("Binance WS error:", e)
            await asyncio.sleep(2)

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
                print("✅ Bybit WS connected")
                async for msg in ws:
                    d = json.loads(msg)
                    if "data" in d:
                        data = d["data"]
                        state["bybit"]["price"] = float(data["markPrice"])
                        state["bybit"]["funding"] = float(data["fundingRate"]) * 100
                        state["bybit"]["next_ts"] = int(data["nextFundingTime"])
        except Exception as e:
            print("Bybit WS error:", e)
            await asyncio.sleep(2)

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
    diff = int(ts / 1000 - time.time())
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
# PRINTER
# =========================
async def printer(state, exchanges):
    while True:
        print("\n" + "-" * 70)
        for ex in exchanges:
            price_str = f"{state[ex]['price']:.6f}" if state[ex]['price'] else "N/A"
            funding_str = f"{state[ex]['funding']:.4f}%" if state[ex]['funding'] is not None else "N/A"
            time_str = time_left(state[ex]['next_ts'])
            print(f"{ex.upper():7} | Price: {price_str} | Funding: {funding_str} | Time Left: {time_str}")
        await asyncio.sleep(1)

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
            "timestamp": int(time.time()*1000)
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
    """Fetch LOT_SIZE stepSize from Binance API"""
    try:
        url = BINANCE_URL + "/fapi/v1/exchangeInfo"
        r = requests.get(url, timeout=5)
        data = r.json()
        
        for s in data.get("symbols", []):
            if s["symbol"] == symbol:
                for f in s.get("filters", []):
                    if f["filterType"] == "LOT_SIZE":
                        return f["stepSize"]
        return "1"  # Default fallback
    except Exception as e:
        print(f"Error fetching Binance filters: {e}")
        return "1"

def round_step_size(quantity, step_size):
    """Round quantity to match stepSize precision"""
    step_size = Decimal(str(step_size))
    quantity = Decimal(str(quantity))
    precision = step_size.normalize().as_tuple().exponent
    if precision < 0:
        precision = abs(precision)
    else:
        precision = 0
    
    # Round down to avoid exceeding balance
    rounded = float(quantity.quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))
    return rounded

def binance_order(symbol, side, qty, step_size):
    try:
        qty = round_step_size(qty, step_size)
        
        print(f"Binance order - Symbol: {symbol}, Side: {side}, Qty: {qty}, StepSize: {step_size}")
        
        params = binance_sign({
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": qty,
            "timestamp": int(time.time()*1000)
        })
        r = requests.post(
            BINANCE_URL + "/fapi/v1/order",
            headers={"X-MBX-APIKEY": BINANCE_KEY},
            params=params,
            timeout=5
        )
        print(f"Binance order response: {r.status_code} - {r.text}")
        return r.json()
    except Exception as e:
        print(f"Binance order error: {e}")
        return {}

# =========================
# BYBIT DEMO EXECUTION (CHANGED FROM TESTNET)
# =========================
BYBIT_KEY = "hfE8R6aHfeEdGX18w7"
BYBIT_SECRET = "AYuExy9gfspxpTBWTZkyHIiyKz8vkdqVqnso"
BYBIT_URL = "https://api-demo.bybit.com"  # ✅ CHANGED TO DEMO

def bybit_sign(params, timestamp):
    if params:
        param_str = timestamp + BYBIT_KEY + "5000" + json.dumps(params)
    else:
        param_str = timestamp + BYBIT_KEY + "5000"
    
    signature = hmac.new(
        BYBIT_SECRET.encode("utf-8"),
        param_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature

def bybit_set_leverage(symbol, lev):
    try:
        timestamp = str(int(time.time() * 1000))
        
        signature = bybit_sign({}, timestamp)
        
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
                
                signature = bybit_sign(params, timestamp)
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
    """Fetch Bybit instrument info for qty step"""
    try:
        url = BYBIT_URL + f"/v5/market/instruments-info?category=linear&symbol={symbol}"
        r = requests.get(url, timeout=5)
        data = r.json()
        
        if data.get("retCode") == 0:
            result = data.get("result", {}).get("list", [])
            if result:
                lot_size_filter = result[0].get("lotSizeFilter", {})
                return lot_size_filter.get("qtyStep", "1")
        return "1"
    except Exception as e:
        print(f"Error fetching Bybit filters: {e}")
        return "1"

def bybit_order(symbol, side, qty, step_size):
    try:
        qty = round_step_size(qty, step_size)
        
        timestamp = str(int(time.time() * 1000))
        
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": "Market",
            "qty": str(qty),
            "timeInForce": "IOC"
        }
        
        signature = bybit_sign(params, timestamp)
        
        headers = {
            "X-BAPI-API-KEY": BYBIT_KEY,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": "5000",
            "Content-Type": "application/json"
        }
        
        print(f"Bybit order - Symbol: {symbol}, Side: {side}, Qty: {qty}, StepSize: {step_size}")
        
        r = requests.post(
            BYBIT_URL + "/v5/order/create",
            headers=headers,
            json=params,
            timeout=5
        )
        print(f"Bybit order response: {r.status_code} - {r.text}")
        return r.json()
    except Exception as e:
        print(f"Bybit order error: {e}")
        return {}

# =========================
# TIME CHECKER
# =========================
def should_execute(ts, target_time_str):
    """Check if current time matches target execution time"""
    if not ts:
        return False
    
    current_time_left = time_left(ts)
    
    try:
        target_h, target_m, target_s = map(int, target_time_str.split(':'))
        target_seconds = target_h * 3600 + target_m * 60 + target_s
        
        current_h, current_m, current_s = map(int, current_time_left.split(':'))
        current_seconds = current_h * 3600 + current_m * 60 + current_s
        
        return abs(current_seconds - target_seconds) <= 1
    except:
        return False

# =========================
# MAIN
# =========================
async def main():
    coin = input("Coin (BTC/ETH/SOL): ").upper()
    exchanges = input("Exchanges (binance,bybit,mexc): ").lower().split(",")
    usdt = float(input("USDT per side: "))
    leverage = int(input("Leverage: "))
    EXECUTION_TIME = input("Execute at funding time left (HH:MM:SS): ")
    MIN_SPREAD = float(input("Minimum funding spread (%): "))

    state = {}
    tasks = []

    if "binance" in exchanges:
        state["binance"] = {"price": 0, "funding": None, "next_ts": None}
        tasks.append(binance_ws(coin + "USDT", state))
    if "bybit" in exchanges:
        state["bybit"] = {"price": 0, "funding": None, "next_ts": None}
        tasks.append(bybit_ws(coin + "USDT", state))
    if "mexc" in exchanges:
        state["mexc"] = {"price": 0, "funding": None, "next_ts": None}
        tasks.append(mexc_rest(coin + "_USDT", state))

    trade_fired = False

    async def execution_watcher():
        nonlocal trade_fired
        print(f"\n⏰ Waiting for execution time: {EXECUTION_TIME} before funding")
        print("📊 Monitoring funding rates...")
        
        # Fetch symbol filters once at start
        binance_symbol = coin + "USDT"
        bybit_symbol = coin + "USDT"
        binance_step = get_binance_symbol_filters(binance_symbol)
        bybit_step = get_bybit_symbol_filters(bybit_symbol)
        
        print(f"📏 Binance stepSize: {binance_step}, Bybit qtyStep: {bybit_step}")
        
        while True:
            if "binance" in exchanges and "bybit" in exchanges:
                if (state["binance"]["next_ts"] and state["bybit"]["next_ts"] and
                    not trade_fired):
                    
                    sig = funding_arbitrage_signal(state, exchanges, MIN_SPREAD)
                    
                    if sig:
                        print(f"\n📈 Signal found: Long {sig['long']} ({state[sig['long']]['funding']:.4f}%), "
                              f"Short {sig['short']} ({state[sig['short']]['funding']:.4f}%), "
                              f"Spread: {sig['spread']:.4f}%")
                    
                    exchange_to_check = "binance" if "binance" in exchanges else "bybit"
                    
                    if should_execute(state[exchange_to_check]["next_ts"], EXECUTION_TIME):
                        if sig and sig['spread'] >= MIN_SPREAD:
                            print(f"\n🚀 EXECUTING HEDGE at {time_left(state[exchange_to_check]['next_ts'])}")
                            print(f"Strategy: Long {sig['long']}, Short {sig['short']}")
                            
                            binance_set_leverage(binance_symbol, leverage)
                            bybit_set_leverage(bybit_symbol, leverage)
                            
                            # Calculate raw quantities
                            qty_b = (usdt * leverage) / state["binance"]["price"]
                            qty_y = (usdt * leverage) / state["bybit"]["price"]
                            
                            print(f"Raw Quantities: Binance={qty_b}, Bybit={qty_y}")
                            
                            # Place orders with proper rounding
                            if sig["long"] == "binance":
                                print(f"Placing Binance BUY order...")
                                binance_order(binance_symbol, "BUY", qty_b, binance_step)
                            else:
                                print(f"Placing Binance SELL order...")
                                binance_order(binance_symbol, "SELL", qty_b, binance_step)
                            
                            if sig["long"] == "bybit":
                                print(f"Placing Bybit Buy order...")
                                bybit_order(bybit_symbol, "Buy", qty_y, bybit_step)
                            else:
                                print(f"Placing Bybit Sell order...")
                                bybit_order(bybit_symbol, "Sell", qty_y, bybit_step)
                            
                            trade_fired = True
                            print("✅ Orders placed! Waiting for next funding period...")
                        else:
                            print(f"❌ No valid signal (spread: {sig['spread'] if sig else 'N/A'}%, "
                                  f"min required: {MIN_SPREAD}%)")
            
            await asyncio.sleep(0.5)

    tasks.append(printer(state, exchanges))
    tasks.append(execution_watcher())
    await asyncio.gather(*tasks)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    asyncio.run(main())