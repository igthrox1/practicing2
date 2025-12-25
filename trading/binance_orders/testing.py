import time                  # Used to generate current timestamp
import hmac                  # Used to create HMAC signature
import hashlib               # Used for SHA256 hashing
import requests              # Used to send HTTP requests to Binance
from urllib.parse import urlencode  # Converts params dict to query string

# =========================
# PUT YOUR TESTNET KEYS
# =========================
API_KEY = "20o5eMr269hIU1Tej94iZUBRoubmfODMeYoGmy60uYaUKydUyeRJdJfzlY3IHq0t"        # Binance Futures Testnet API Key
API_SECRET = "djPGrUCip9ITZdsVxHoc6SWCnfQK6LcrNn7GiVOLHTbynsHYUMORVM28BhzmF6r7"     # Binance Futures Testnet Secret Key

# Base URL for Binance USDT-M Futures Testnet
BASE_URL = "https://testnet.binancefuture.com"

# -------------------------------------------------
# Function to sign request parameters
# -------------------------------------------------
def sign_params(params, secret):
    # Convert parameters to URL query string format
    query_string = urlencode(params)

    # Create HMAC-SHA256 signature using secret key
    signature = hmac.new(
        secret.encode("utf-8"),          # Secret key (bytes)
        query_string.encode("utf-8"),    # Query string (bytes)
        hashlib.sha256                   # Hashing algorithm
    ).hexdigest()

    # Add signature to parameters
    params["signature"] = signature

    return params

# -------------------------------------------------
# Function to test Binance Futures Testnet connection
# -------------------------------------------------
def test_connection():
    print("🔄 Testing Binance Futures Testnet connection...")

    # Binance requires timestamp in milliseconds
    params = {
        "timestamp": int(time.time() * 1000)
    }

    # Sign parameters with API secret
    signed_params = sign_params(params, API_SECRET)

    # API key must be passed in request headers
    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    # Futures account endpoint (private endpoint)
    url = BASE_URL + "/fapi/v2/account"

    # Send GET request to Binance
    response = requests.get(url, headers=headers, params=signed_params)

    # Print HTTP status and response data
    print("HTTP Status:", response.status_code)
    print("Response:")
    print(response.json())

# -------------------------------------------------
# Entry point of the script
# -------------------------------------------------
if __name__ == "__main__":
    test_connection()