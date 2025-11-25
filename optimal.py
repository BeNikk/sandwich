from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature
import asyncio
import json
import time
import os 
from dotenv import load_dotenv

class OptimizedDEXScanner:
    def __init__(self, rpc_url: str):
        self.client = AsyncClient(rpc_url)
        
        self.dex_programs = {
            'raydium_clmm': "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK", 
            'orca_whirlpool': "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
        }
        
        self.stats = {
            'rpc_calls': 0,
            'successful_fetches': 0,
            'failed_fetches': 0
        }
    
    async def get_dex_transactions_optimized(self, limit: int = 1000):
        all_dex_signatures = []
        
        for dex_name, program_id in self.dex_programs.items():
            print(f"Fetching {dex_name} signatures...")
            
            try:
                # CHANGE 1: Use 'finalized' commitment to ensure transactions exist
                signatures = await self.client.get_signatures_for_address(
                    Pubkey.from_string(program_id),
                    limit=limit // len(self.dex_programs),
                    commitment="finalized"  # Changed from "confirmed"
                )
                self.stats['rpc_calls'] += 1
                
                if signatures.value:
                    valid_signatures = 0
                    for sig_info in signatures.value:
                        if not sig_info.err:
                            # CHANGE 2: Filter out very recent transactions (last 5 minutes)
                            if sig_info.block_time and sig_info.block_time < (time.time() - 300):
                                all_dex_signatures.append({
                                    'signature': str(sig_info.signature),
                                    'slot': sig_info.slot,
                                    'dex': dex_name,
                                    'timestamp': sig_info.block_time,
                                    'fee': getattr(sig_info, 'fee', 0)
                                })
                                valid_signatures += 1
                    
                    print(f"Found {len(signatures.value)} total, {valid_signatures} valid {dex_name} signatures")
                else:
                    print(f"No signatures returned for {dex_name}")
                
            except Exception as e:
                print(f"Error fetching {dex_name}: {e}")
                import traceback
                traceback.print_exc()
        
        all_dex_signatures.sort(key=lambda x: x['slot'])
        print(f"Total valid signatures: {len(all_dex_signatures)}")
        return all_dex_signatures
    
    async def fetch_full_transactions(self, signatures_list: list, batch_size: int = 3):
        if not signatures_list:
            print("No signatures to fetch")
            return []
            
        full_transactions = []
        total_batches = (len(signatures_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(signatures_list), batch_size):
            batch = signatures_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"Processing batch {batch_num}/{total_batches}: {len(batch)} transactions")
            
            for sig_info in batch:
                try:
                    signature_obj = Signature.from_string(sig_info['signature'])
                    
                    # CHANGE 3: Use finalized commitment and add retry logic
                    result = await self.client.get_transaction(
                        signature_obj,
                        encoding="jsonParsed",
                        commitment="finalized",  # Added commitment
                        max_supported_transaction_version=0
                    )
                    self.stats['rpc_calls'] += 1
                    
                    print(f"DEBUG - {sig_info['signature'][:16]}... (slot: {sig_info['slot']})")
                    print(f"  result.value exists: {result.value is not None}")
                    
                    if result.value:
                        print(f"  has meta: {hasattr(result.value, 'meta')}")
                        if hasattr(result.value, 'meta'):
                            print(f"  meta exists: {result.value.meta is not None}")
                            if result.value.meta:
                                print(f"  meta.err: {result.value.meta.err}")
                        
                        # More lenient success condition
                        transaction_failed = False
                        if hasattr(result.value, 'meta') and result.value.meta and result.value.meta.err:
                            transaction_failed = True
                        
                        if not transaction_failed:
                            tx_data = {
                                'signature': sig_info['signature'],
                                'slot': sig_info['slot'],
                                'dex': sig_info['dex'],
                                'timestamp': sig_info['timestamp'],
                                'fee': sig_info['fee'],
                                'transaction': result.value
                            }
                            full_transactions.append(tx_data)
                            self.stats['successful_fetches'] += 1
                            print(f"  ✅ SUCCESS")
                        else:
                            self.stats['failed_fetches'] += 1
                            print(f"  ❌ FAILED - Transaction has error: {result.value.meta.err}")
                    else:
                        self.stats['failed_fetches'] += 1
                        print(f"  ❌ FAILED - No result.value (transaction not found)")
                        
                        # CHANGE 4: Try alternative method if transaction not found
                        print(f"  Trying alternative fetch method...")
                        try:
                            alt_result = await self.client.get_transaction(
                                signature_obj,
                                encoding="json",  # Try different encoding
                                commitment="finalized"
                            )
                            if alt_result.value:
                                print(f"  Alternative method found transaction!")
                            else:
                                print(f"  Alternative method also failed")
                        except Exception as alt_e:
                            print(f"  Alternative method error: {alt_e}")
                        
                except Exception as e:
                    print(f"Failed to fetch {sig_info['signature'][:16]}...: {e}")
                    self.stats['failed_fetches'] += 1
                
                await asyncio.sleep(0.2)  # Slower to avoid rate limits
            
            print(f"Batch {batch_num} complete: {len(full_transactions)} total successful")
            
            if len(full_transactions) >= 3:
                print("Got 3 successful transactions, stopping for debugging...")
                break
                
            await asyncio.sleep(0.5)
        
        return full_transactions
    
    def extract_swap_details(self, transaction):
        try:
            swap_info = {
                'signer': 'unknown',
                'sol_change': 0,
                'token_changes': [],
                'instructions': [],
                'debug': str(type(transaction))
            }
            
            # Try to extract signer
            try:
                if hasattr(transaction, 'transaction') and hasattr(transaction.transaction, 'message'):
                    message = transaction.transaction.message
                    if hasattr(message, 'account_keys') and len(message.account_keys) > 0:
                        swap_info['signer'] = str(message.account_keys[0])
            except:
                pass
            
            return swap_info
            
        except Exception as e:
            return {'error': str(e), 'debug': str(type(transaction))}
    
    def save_results(self, transactions, filename=None):
        if not filename:
            timestamp = int(time.time())
            filename = f"optimized_dex_transactions_{timestamp}.json"
        
        data = {
            'metadata': {
                'timestamp': time.time(),
                'total_transactions': len(transactions),
                'rpc_stats': self.stats,
                'dex_breakdown': {}
            },
            'transactions': []
        }
        
        for tx in transactions:
            swap_details = self.extract_swap_details(tx['transaction'])
            
            tx_record = {
                'signature': tx['signature'],
                'slot': tx['slot'],
                'dex': tx['dex'],
                'timestamp': tx['timestamp'],
                'fee': tx['fee'],
                'swap_details': swap_details
            }
            data['transactions'].append(tx_record)
            
            if tx['dex'] not in data['metadata']['dex_breakdown']:
                data['metadata']['dex_breakdown'][tx['dex']] = 0
            data['metadata']['dex_breakdown'][tx['dex']] += 1
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Results saved to: {filename}")
        return filename

async def main():
    load_dotenv()
    api_key = os.getenv('HELIUS_API_KEY')
    if not api_key:
        print("Error: HELIUS_API_KEY not found in .env file")
        print("Create a .env file with: HELIUS_API_KEY=your_key_here")
        return
    
    helius_rpc = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
    
    scanner = OptimizedDEXScanner(helius_rpc)
    
    print("Starting optimized DEX transaction scan...")
    start_time = time.time()
    
    try:
        # CHANGE 5: Get more signatures but filter better
        dex_signatures = await scanner.get_dex_transactions_optimized(100)
        
        if dex_signatures:
            print(f"Fetching full transaction data for {len(dex_signatures)} signatures...")
            # Test fewer transactions first
            full_transactions = await scanner.fetch_full_transactions(dex_signatures[:15])
            
            end_time = time.time()
            scan_time = end_time - start_time
            
            print(f"\nScan completed in {scan_time:.2f} seconds")
            print(f"Total RPC calls: {scanner.stats['rpc_calls']}")
            print(f"Successful fetches: {scanner.stats['successful_fetches']}")
            print(f"Failed fetches: {scanner.stats['failed_fetches']}")
            if scanner.stats['successful_fetches'] + scanner.stats['failed_fetches'] > 0:
                print(f"Success rate: {scanner.stats['successful_fetches']/(scanner.stats['successful_fetches']+scanner.stats['failed_fetches'])*100:.1f}%")
            print(f"DEX transactions found: {len(full_transactions)}")
            
            if full_transactions:
                filename = scanner.save_results(full_transactions)
                
                print(f"✅ Successfully saved {len(full_transactions)} transactions")
                print(f"📁 File: {filename}")
                
                return full_transactions
            else:
                print("No successful transaction fetches - transactions may be too recent or not available")
        else:
            print("No DEX signatures found")
            
    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scanner.client.close()
    
    return []

if __name__ == "__main__":
    asyncio.run(main())