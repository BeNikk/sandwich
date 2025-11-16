import asyncio
import os 
import utils
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient

RAYDIUM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
ORCA_PROGRAM_ID = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"

async def main():
    load_dotenv()
    api_key = os.getenv('HELIUS_API_KEY')
    if not api_key:
        print("Error: HELIUS_API_KEY not found")
        return
    helius_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"

    async with AsyncClient(helius_url) as client:
        res = await client.is_connected()
        print(f"Connected: {res}\n")
        
        slot_response = await client.get_slot()
        current_slot = slot_response.value
        print(f"Current slot: {current_slot}")
        
        print(f"Fetching blocks for DEX txns...\n")
        dex_txs = await utils.scan_multiple_blocks(client, num_blocks=50)

        raydium_count = len([tx for tx in dex_txs if tx['dex'] == 'Raydium'])
        orca_count = len([tx for tx in dex_txs if tx['dex'] == 'Orca'])
        
        print(f"\n--- Summary ---")
        print(f"Total DEX transactions found: {len(dex_txs)}")
        print(f"Raydium: {raydium_count}")
        print(f"Orca: {orca_count}")
        
        print(f"\n--- First 5 Examples ---")
        for i, tx in enumerate(dex_txs[:5]):
            print(f"{i+1}. {tx['dex']} in slot {tx['slot']}: {tx['signature'][:]}...")
asyncio.run(main())