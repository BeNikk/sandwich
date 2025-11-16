# Sandwich attack is nothing but
# bot buys A <->B (frontrun)
# victim buys A <-> B
# bot sells B <-> A (backrun)

def find_matching_token_pair(tx1, tx2):

    same_direction = (tx1['token_in'] == tx2['token_in'] and 
                     tx1['token_out'] == tx2['token_out'])
    
    opposite_direction = (tx1['token_in'] == tx2['token_out'] and 
                         tx1['token_out'] == tx2['token_in'])
    
    return same_direction, opposite_direction


def detect_sandwiches(dex_txs):

    sorted_txs = sorted(dex_txs, key=lambda x: x['slot'])
    sandwiches = []
    
    unique_signers = set(tx['signer'] for tx in sorted_txs)
    print(f"   Total transactions: {len(sorted_txs)}")
    print(f"   Unique signers: {len(unique_signers)}")
    print(f"   Slot range: {sorted_txs[0]['slot']} to {sorted_txs[-1]['slot']}")
    
    print(f"\n   First 3 signers:")
    for i, tx in enumerate(sorted_txs[:3]):
        print(f"   {i+1}. {tx['signer'][:50]}...")
    
    token_pairs = {}
    for tx in sorted_txs:
        pair = f"{tx['token_in'][:8]}->{tx['token_out'][:8]}"
        token_pairs[pair] = token_pairs.get(pair, 0) + 1
    
    print(f"\n   Token pairs with multiple trades:")
    for pair, count in token_pairs.items():
        if count > 1:
            print(f"   {pair}: {count} trades")
    
    
    total_frontruns_found = 0
    
    for i, victim_tx in enumerate(sorted_txs):
        victim_slot = victim_tx['slot']
        victim_signer = victim_tx['signer']

        potential_frontruns = []
        
        for j in range(i):
            candidate = sorted_txs[j]
            slot_diff = victim_slot - candidate['slot']
            
            if slot_diff >= 1 and slot_diff <= 3:
                if candidate['signer'] != victim_signer:
                    same_dir, opp_dir = find_matching_token_pair(candidate, victim_tx)
                    if same_dir:
                        potential_frontruns.append(candidate)
                        total_frontruns_found += 1
        
        for frontrun in potential_frontruns:
            bot_signer = frontrun['signer']
            
            for k in range(i + 1, len(sorted_txs)):
                candidate = sorted_txs[k]
                slot_diff = candidate['slot'] - victim_slot
                
                if slot_diff >= 1 and slot_diff <= 5:
                    if candidate['signer'] == bot_signer:
                        same_dir, opp_dir = find_matching_token_pair(candidate, victim_tx)
                        if opp_dir:
                            sandwich = {
                                'frontrun': frontrun,
                                'victim': victim_tx,
                                'backrun': candidate,
                                'bot_address': bot_signer,
                                'slot_span': candidate['slot'] - frontrun['slot'],
                                'token_pair': f"{victim_tx['token_in'][:8]}.../{victim_tx['token_out'][:8]}..."
                            }
                            sandwiches.append(sandwich)
                            
                            print(f" sandwich attack detected #{len(sandwiches)}:")
                            print(f"   Bot: {bot_signer[:16]}...")
                            print(f"   Frontrun  (slot {frontrun['slot']}): {frontrun['signature'][:16]}...")
                            print(f"   Victim    (slot {victim_tx['slot']}): {victim_tx['signature'][:16]}...")
                            print(f"   Backrun   (slot {candidate['slot']}): {candidate['signature'][:16]}...")
                            print(f"   Slot span: {sandwich['slot_span']} slots")
                            print(f"   Token pair: {sandwich['token_pair']}\n")
                            break
    
    print(f"   Potential front-runs found: {total_frontruns_found}")
    print(f"   Complete sandwiches found: {len(sandwiches)}")
    
    return sandwiches