import aiohttp
import asyncio

url = 'https://api.binance.com/api/v3/ticker/price'
params = {'symbol' : 'BTCUSDT'}

async def fetch_price(session , url , params):
    try:
        async with session.get(url , params= params) as response:
            data = await response.json()
            price = float(data['price'])
            print("BTC price is :",price) 
    except Exception as e:
        print("Error is :",e)

async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            await fetch_price(session, url , params)

asyncio.run(main())