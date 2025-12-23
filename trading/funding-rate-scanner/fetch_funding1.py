from symbol_formatter import format_symbol
from exchange_url import EXCHANGES
import aiohttp
import asyncio

async def fetch_funding(session, exchange, coin):
    symbol = format_symbol(exchange, coin)

    if exchange == "binance":
        params = {"symbol": symbol, "limit": 1}
        async with session.get(EXCHANGES[exchange]["url"], params=params) as r:
            data = await r.json()
            return float(data[-1]["fundingRate"]) * 100

    if exchange == "bybit":
        params = {"category": "linear", "symbol": symbol, "limit": 1}
        async with session.get(EXCHANGES[exchange]["url"], params=params) as r:
            data = await r.json()
            return float(data["result"]["list"][0]["fundingRate"]) * 100

    if exchange == "mexc":
        params = {"symbol": symbol}
        async with session.get(EXCHANGES[exchange]["url"], params=params) as r:
            data = await r.json()
            return float(data["data"]["fundingRate"]) * 100
        
