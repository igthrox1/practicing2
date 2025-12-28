import requests
import time
import hmac
import hashlib
import urllib.parse

KEY = "hfE8R6aHfeEdGX18w7"
SECRET = "AYuExy9gfspxpTBWTZkyHIiyKz8vkdqVqnso"

print("🔐 Fixing signature...")

# Get timestamp
timestamp = str(int(time.time() * 1000))
print(f"Timestamp: {timestamp}")

# Parameters MUST be in alphabetical order including ALL params
# accountType comes BEFORE api_key alphabetically!
params_dict = {
    "accountType": "UNIFIED",
    "api_key": KEY,
    "recv_window": "5000",
    "timestamp": timestamp
}

# Sort keys alphabetically
sorted_keys = sorted(params_dict.keys())
print(f"Sorted keys: {sorted_keys}")

# Build parameter string
param_string = "&".join([f"{k}={params_dict[k]}" for k in sorted_keys])
print(f"Param string: {param_string}")

# Generate signature
signature = hmac.new(
    SECRET.encode('utf-8'),
    param_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"Signature: {signature[:20]}...")

# Build URL
base_url = "https://api-demo.bybit.com"
url = f"{base_url}/v5/account/wallet-balance?{param_string}&sign={signature}"
print(f"\n🌐 URL: {url[:100]}...")

# Send request
response = requests.get(url)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")