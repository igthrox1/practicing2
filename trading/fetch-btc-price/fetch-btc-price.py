import requests 

url = "https://api.binance.com/api/v3/ticker/price"
params = {"symbol" : "BTCUSDT"}

response = requests.get(url , params = params)
data = response.json()

try: 
    response = requests.get(url, params = params , timeout=5)
    response.raise_for_status()
    data = response.json()
    price = float(data['price'])
    print(f"current BTC price is : {price} USDT")
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print("HTTP error :",e)
except ValueError:
    print("Error parsing price value")
except Exception as e :
    print("Unknown error :",e)