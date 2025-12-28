from pybit.unified_trading import HTTP

KEY = "hfE8R6aHfeEdGX18w7"
SECRET = "AYuExy9gfspxpTBWTZkyHIiyKz8vkdqVqnso"

session = HTTP(demo=True, api_key=KEY, api_secret=SECRET)

# Try different endpoints
tests = [
    ("Balance", session.get_wallet_balance, {"accountType": "UNIFIED"}),
    ("Position", session.get_positions, {"category": "linear", "symbol": "BTCUSDT"}),
    ("Symbol Info", session.get_instruments_info, {"category": "linear", "symbol": "BTCUSDT"}),
]

for name, func, params in tests:
    print(f"\n📊 Testing {name}...")
    try:
        result = func(**params)
        if result['retCode'] == 0:
            print(f"✅ {name}: OK")
        else:
            print(f"❌ {name}: {result['retMsg']}")
    except Exception as e:
        print(f"❌ {name}: Error - {e}")