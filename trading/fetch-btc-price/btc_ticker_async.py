import asyncio 
import aiohttp 

url = "https://api.binance.com/api/v3/ticker/price"
params = {"symbol" : "BTCUSDT"}

async def fetch_price(url,params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url , params = params) as resp:
            data = await resp.json()
            print("BTCUSDT",data['price'])

asyncio.run(fetch_price(url,params))
