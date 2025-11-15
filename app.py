import asyncio
import os 
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient

async def main():
    load_dotenv()
    api_key = os.getenv('HELIUS_API_KEY')
    if not api_key:
        print("Error: HELIUS_API_KEY not found in environment variables")
        return
    helius_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"

    async with AsyncClient(helius_url) as client:
        res = await client.is_connected()
    print(res)  # True

asyncio.run(main())