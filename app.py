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
        print(f"Connected: {res}")
        slot_response = await client.get_slot()
        current_slot = slot_response.value
        print(f"\nCurrent slot: {current_slot}")
        block_response = await client.get_block(
            current_slot,
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )
        if block_response.value:
            block = block_response.value
            print(f"Block has {len(block.transactions)} transactions")
            
            if block.transactions:
                first_tx = block.transactions[0]
                print(f"\n--- First Transaction ---")
                print(f"Signature: {first_tx.transaction.signatures[0]}")
                print(f"Success: {first_tx.meta.err is None}")
                print(f"Number of instructions: {len(first_tx.transaction.message.instructions)}")
        else:
            print("Block was empty or skipped")

    print(res)

asyncio.run(main())