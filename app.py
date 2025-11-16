import asyncio
import os 
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient

RAYDIUM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
ORCA_PROGRAM_ID = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"

def is_dex_transaction(transaction):
    try:
        instructions = transaction.transaction.message.instructions
        
        for instruction in instructions:
            if hasattr(instruction, 'program_id'):
                program_id = str(instruction.program_id)
                
                if program_id == RAYDIUM_PROGRAM_ID:
                    return True, "Raydium"
                elif program_id == ORCA_PROGRAM_ID:
                    return True, "Orca"
        
        return False, None
    except Exception as e:
        return False, None

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
        
        print(f"Fetching block...\n")
        block_response = await client.get_block(
            current_slot,
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )
        
        if not block_response.value:
            print("Block was empty or skipped")
            return
        
        block = block_response.value
        print(f"Total transactions in block: {len(block.transactions)}")
        
        dex_count = 0
        raydium_count = 0
        orca_count = 0
        
        print("\n--- Scanning for DEX transactions ---")
        
        for tx in block.transactions:
            is_dex, dex_name = is_dex_transaction(tx)
            
            if is_dex:
                dex_count += 1
                signature = str(tx.transaction.signatures[0])
                
                if dex_name == "Raydium":
                    raydium_count += 1
                elif dex_name == "Orca":
                    orca_count += 1
                
                print(f"{dex_count}. {dex_name} swap: {signature[:]} ...")
                
                if dex_count >= 5:
                    print("... (stopping after 5 to keep output clean)")
                    break
        
        print(f"\n--- Summary ---")
        print(f"Total DEX transactions found: {dex_count}")
        print(f"Raydium: {raydium_count}")
        print(f"Orca: {orca_count}")

asyncio.run(main())