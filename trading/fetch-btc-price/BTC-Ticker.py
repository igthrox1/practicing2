import time 
import requests 

url = "https://api.binance.com/api/v3/ticker/price"
params = {"symbol" : "BTCUSDT"}

while True:
    response = requests.get(url , params = params)
    price=response.json()['price']
    print("BTCUSDT" , price)
    print("--------------")
    time.sleep(0.5)