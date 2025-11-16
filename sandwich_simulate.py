def find_simulatable_sandwiches(dex_txs):
    
    sorted_txs = sorted(dex_txs, key=lambda x: x['slot'])
    simulations = []
    
    # Finding any 3 transactions with same token pair in the pattern:
    for i in range(len(sorted_txs) - 2):
        tx1 = sorted_txs[i]
        
        for j in range(i + 1, len(sorted_txs)):
            tx2 = sorted_txs[j]
            
            if tx2['slot'] - tx1['slot'] > 3:
                break
            
            if (tx1['token_in'] == tx2['token_in'] and 
                tx1['token_out'] == tx2['token_out']):
                
                for k in range(j + 1, len(sorted_txs)):
                    tx3 = sorted_txs[k]
                    
                    if tx3['slot'] - tx2['slot'] > 3:
                        break
                    
                    if (tx3['token_in'] == tx2['token_out'] and 
                        tx3['token_out'] == tx2['token_in']):
                        
                        simulation = {
                            'frontrun': tx1,
                            'victim': tx2,
                            'backrun': tx3,
                            'slot_span': tx3['slot'] - tx1['slot']
                        }
                        simulations.append(simulation)
                        
                        if len(simulations) <= 3: 
                            print(f"\n Simulatable Sandwich Pattern #{len(simulations)}:")
                            print(f"   Slot {tx1['slot']}: Buy  {tx1['amount_in']:.4f} {tx1['token_in'][:8]}... "
                                  f"→ {tx1['amount_out']:.4f} {tx1['token_out'][:8]}...")
                            print(f"   Slot {tx2['slot']}: Buy  {tx2['amount_in']:.4f} {tx2['token_in'][:8]}... "
                                  f"→ {tx2['amount_out']:.4f} {tx2['token_out'][:8]}... (VICTIM)")
                            print(f"   Slot {tx3['slot']}: Sell {tx3['amount_in']:.4f} {tx3['token_in'][:8]}... "
                                  f"→ {tx3['amount_out']:.4f} {tx3['token_out'][:8]}...")
                        
                        break
                break
    
    print(f"\nFound {len(simulations)} simulatable sandwich patterns")
    return simulations


def calculate_sandwich_profit(simulation):

    frontrun = simulation['frontrun']
    victim = simulation['victim']
    backrun = simulation['backrun']
    
    base_token = frontrun['token_in']
    
    if base_token == backrun['token_out']:
        cost = frontrun['amount_in']
        
        revenue = backrun['amount_out']
        
        profit = revenue - cost
        profit_percent = (profit / cost * 100) if cost > 0 else 0
        
        return {
            'base_token': base_token,
            'cost': cost,
            'revenue': revenue,
            'profit': profit,
            'profit_percent': profit_percent,
            'victim_impact': victim['amount_in']
        }
    
    return None


def analyze_simulations(simulations):
    
    analyzed = []
    
    for i, sim in enumerate(simulations[:3], 1):
        profit_data = calculate_sandwich_profit(sim)
        
        if profit_data:
            analyzed.append({
                'simulation': sim,
                'profit_data': profit_data
            })
            
            print(f"Example #{i}:")
            print(f"  Slot Span: {sim['slot_span']} slots")
            print(f"  Base Token: {profit_data['base_token'][:16]}...")
            print(f"  ")
            print(f"  Bot's Trade:")
            print(f"    - Front-run cost:  {profit_data['cost']:.6f}")
            print(f"    - Back-run revenue: {profit_data['revenue']:.6f}")
            print(f"    - Profit:           {profit_data['profit']:.6f} "
                  f"({profit_data['profit_percent']:.2f}%)")
            print(f"  ")
            print(f"  Victim Impact:")
            print(f"    - Victim spent:     {profit_data['victim_impact']:.6f}")
            print(f"    - Extracted value:  ~{profit_data['profit']:.6f}")
            print(f"  ")
            print(f"  Transactions:")
            print(f"    - Frontrun:  {sim['frontrun']['signature']}")
            print(f"    - Victim:    {sim['victim']['signature']}")
            print(f"    - Backrun:   {sim['backrun']['signature']}")
    
    return analyzed


def generate_sandwich_report(dex_txs):
    simulations = find_simulatable_sandwiches(dex_txs)
    
    if simulations:
        analyzed = analyze_simulations(simulations)
        return analyzed
    else:
        print(f"\n  Not enough transaction patterns for simulation")
        return []