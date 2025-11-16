import asyncio
import os 
import utils
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
import json

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
        
        print(f"Fetching blocks for DEX txns ...\n")
        dex_txs = await utils.scan_multiple_blocks(client, num_blocks=50)

        raydium_count = len([tx for tx in dex_txs if tx['dex'] == 'Raydium'])
        orca_count = len([tx for tx in dex_txs if tx['dex'] == 'Orca'])
        
        print(f"\n Summary  ")
        print(f"Total DEX transactions found: {len(dex_txs)}")
        print(f"Raydium: {raydium_count}")
        print(f"Orca: {orca_count}")
        if dex_txs:
            print(json.dumps(dex_txs[0], indent=2))
            sample = dex_txs[0]
            print(f"Signer: {sample['signer'][:16]}...")
            print(f"Swapped: {sample['amount_in']:.4f} of token {sample['token_in'][:16]}...")
            print(f"Got: {sample['amount_out']:.4f} of token {sample['token_out'][:16]}...")
        
        with open('dex_transactions.json', 'w') as f:
            json.dump(dex_txs, f, indent=2)
        print(f"\n Saved {len(dex_txs)} transactions to dex_transactions.json")
        
asyncio.run(main())