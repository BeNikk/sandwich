import asyncio

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


async def scan_multiple_blocks(client, num_blocks=50):
    slot_response = await client.get_slot()
    current_slot = slot_response.value
    
    all_dex_txs = []
    
    for i in range(num_blocks):
        slot = current_slot - i
        
        try:
            block_response = await client.get_block(
                slot,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            
            if not block_response.value:
                continue 
            
            block = block_response.value
            
            for tx in block.transactions:
                is_dex, dex_name = is_dex_transaction(tx)
                
                if is_dex:
                    dex_tx = {
                        'slot': slot,
                        'signature': str(tx.transaction.signatures[0]),
                        'dex': dex_name,
                        'transaction': tx
                    }
                    all_dex_txs.append(dex_tx)
            
            await asyncio.sleep(0.05)
            
        except Exception as e:
            continue
    
    return all_dex_txs