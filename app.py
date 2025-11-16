import asyncio
import os 
import utils
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
import json
import sandwich
import sandwich_simulate
import pnl

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
        dex_txs = await utils.scan_multiple_blocks(client, num_blocks=200)

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
        sandwiches = sandwich.detect_sandwiches(dex_txs)

        print(f"Total transactions analyzed: {len(dex_txs)}")
        print(f"Sandwich attacks found: {len(sandwiches)}")
        
        if len(sandwiches) > 0:
            with open('sandwich_attacks.json', 'w') as f:
                json.dump(sandwiches, f, indent=2)
            print(f"\n Saved {len(sandwiches)} sandwiches to sandwich_attacks.json")

            if sandwiches:
                print(f"\n first sandwich attack details")
                s = sandwiches[0]
                print(json.dumps(s, indent=2))
                top_5, summary = pnl.main()
                print(f"   - DEX transactions collected: {len(dex_txs)}")
                print(f"   - Sandwiches detected: {len(sandwiches)}")
                print(f"   - Profitable sandwiches: {summary['profitable_count']}")
                print(f"   - Total value extracted: {summary.get('total_profit_extracted', 0):.6f} SOL")
            
           
        else:
            print(f"\n No sandwiches detected in this dataset")

        #simulate if not found any sandwich attacks
        if len(sandwiches) == 0:
            analyzed = sandwich_simulate.generate_sandwich_report(dex_txs)
            
            if analyzed:
                simulation_output = []
                for item in analyzed:
                    simulation_output.append({
                        'frontrun_slot': item['simulation']['frontrun']['slot'],
                        'victim_slot': item['simulation']['victim']['slot'],
                        'backrun_slot': item['simulation']['backrun']['slot'],
                        'frontrun_sig': item['simulation']['frontrun']['signature'],
                        'victim_sig': item['simulation']['victim']['signature'],
                        'backrun_sig': item['simulation']['backrun']['signature'],
                        'profit': item['profit_data']['profit'],
                        'profit_percent': item['profit_data']['profit_percent'],
                        'base_token': item['profit_data']['base_token']
                    })
                
                with open('sandwich_simulations.json', 'w') as f:
                    json.dump(simulation_output, f, indent=2)
                print(f"\n Saved simulations to sandwich_simulations.json")


asyncio.run(main())