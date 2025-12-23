from fetch_funding1 import fetch_funding
import aiohttp
import asyncio

async def main():
    coin = input("Enter coin (BTC/ETH/etc): ").strip()
    exchanges = input("Enter exchanges (comma separated): ").lower().split(",")

    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [
                fetch_funding(session, ex.strip(), coin)
                for ex in exchanges
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            print(f"\n{coin} Funding Rates")
            for ex, rate in zip(exchanges, results):
                if isinstance(rate, Exception):
                    print(f"{ex.upper():<8}: ERROR")
                else:
                    print(f"{ex.upper():<8}: {rate:+.4f}%")

            await asyncio.sleep(5)

asyncio.run(main())