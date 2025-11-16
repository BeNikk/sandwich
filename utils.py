import asyncio
from config import RAYDIUM_PROGRAM_ID,ORCA_PROGRAM_ID

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


def extract_signer(transaction): 
    try:
        accounts = transaction.transaction.message.account_keys
        if accounts and len(accounts) > 0:
            return str(accounts[0]) # because first account is the signer, this is to check and match the bot's address as here bot has to be the signer
        
        return None
    except:
        return None

async def scan_multiple_blocks(client, num_blocks=50):
    slot_response = await client.get_slot()
    current_slot = slot_response.value
    
    all_dex_txs = []
    blocks_checked = 0

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

            blocks_checked += 1            
            block = block_response.value
            
            for tx in block.transactions:
                is_dex, dex_name = is_dex_transaction(tx)
                
                if is_dex:
                    signer = extract_signer(tx) #signer is the one who paid the fees
                    token_data = extract_token_changes(tx) # this is getting back the tokens in and out 
                    if signer and token_data:
                        dex_tx = {
                        'slot': slot,
                        'signature': str(tx.transaction.signatures[0]),
                        'dex': dex_name,
                        'signer':signer,
                        'token_in':token_data['token_in'],
                        'token_out':token_data['token_out'],
                        'amount_in':token_data['amount_in'],
                        'amount_out':token_data['amount_out']                        
                        }
                        all_dex_txs.append(dex_tx)

            await asyncio.sleep(0.05)
            
        except Exception as e:
            continue
    
    return all_dex_txs

def extract_token_changes(transaction):
    try:
        meta = transaction.meta
        
        token_changes = {}
        
        if hasattr(meta, 'pre_token_balances'):
            for pre in meta.pre_token_balances:
                if hasattr(pre, 'mint') and hasattr(pre, 'ui_token_amount'):
                    mint = str(pre.mint)
                    amount = pre.ui_token_amount.ui_amount or 0
                    token_changes[mint] = {'pre': amount, 'post': 0}
        
        if hasattr(meta, 'post_token_balances'):
            for post in meta.post_token_balances:
                if hasattr(post, 'mint') and hasattr(post, 'ui_token_amount'):
                    mint = str(post.mint)
                    amount = post.ui_token_amount.ui_amount or 0
                    
                    if mint in token_changes:
                        token_changes[mint]['post'] = amount
                    else:
                        token_changes[mint] = {'pre': 0, 'post': amount}
        
        token_in = None  # this is for what the user/bot sold or swapped
        token_out = None # this is for what the user/bot bought
        amount_in = 0
        amount_out = 0
        
        for mint, balances in token_changes.items():
            change = balances['post'] - balances['pre']
            
            if change < -0.0001:
                token_in = mint
                amount_in = abs(change)
            elif change > 0.0001:
                token_out = mint
                amount_out = change
        
        if token_in and token_out:
            return {
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': amount_in,
                'amount_out': amount_out
            }
        
        return None
        
    except Exception as e:
        return None