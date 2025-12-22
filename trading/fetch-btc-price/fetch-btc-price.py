import requests 
import time

url = "https://api.binance.com/api/v3/ticker/price"
params = {"symbol" : "BTCUSDT"}

response = requests.get(url , params = params)
data = response.json()

try: 
    start_time = time.time() 
    response = requests.get(url, params = params , timeout=5)
    response.raise_for_status()
    data = response.json()
    price = float(data['price'])
    print(f"current BTC price is : {price} USDT")
    end_time = time.time() 
    response_time = end_time - start_time
    print("response time is : ",response_time)

except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print("HTTP error :",e)
except ValueError:
    print("Error parsing price value")
except Exception as e :
    print("Unknown error :",e)