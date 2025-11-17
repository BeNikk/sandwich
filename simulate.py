import json

def find_wide_sandwiches(dex_txs):
    try:
        with open('sandwich_attacks.json', 'r') as f:
            sandwiches = json.load(f)
    except FileNotFoundError:
        print("Error: sandwich_attacks.json not found. Run app.py first!")
        return []
    
    wide_sandwiches = [s for s in sandwiches if s.get('slot_span', 0) > 1]
    
    print(f"Total sandwiches detected: {len(sandwiches)}")
    print(f"Wide sandwiches (multi-slot): {len(wide_sandwiches)}")
    print(f"Single-slot sandwiches: {len(sandwiches) - len(wide_sandwiches)}")
    
    simulations = []
    for i, sandwich in enumerate(wide_sandwiches[:3], 1):
        print("Wide sandwich example")
        frontrun = sandwich['frontrun']
        victim = sandwich['victim']
        backrun = sandwich['backrun']
        
        print(f"\nBot Address: {sandwich['bot_address']}")
        print(f"Slot Span: {sandwich['slot_span']} slots (WIDE ATTACK)")
        
        print(f"\n[slot {frontrun['slot']}] frontrun")
        print(f"  Signature: {frontrun['signature']}")
        print(f"  Action: Bot buys token")
        print(f"  Token IN:  {frontrun['token_in'][:16]}...")
        print(f"  Amount IN: {frontrun['amount_in']:.6f}")
        print(f"  Token OUT: {frontrun['token_out'][:16]}...")
        print(f"  Amount OUT: {frontrun['amount_out']:.6f}")
        
        print(f"\n[SLOT {victim['slot']}] VICTIM TRANSACTION:")
        print(f"  Signature: {victim['signature']}")
        print(f"  Victim: {victim['signer'][:20]}...")
        print(f"  Action: User buys same token (worse price)")
        print(f"  Token IN:  {victim['token_in'][:16]}...")
        print(f"  Amount IN: {victim['amount_in']:.6f}")
        print(f"  Token OUT: {victim['token_out'][:16]}...")
        print(f"  Amount OUT: {victim['amount_out']:.6f}")
        
        print(f"\n[SLOT {backrun['slot']}] BACKRUN:")
        print(f"  Signature: {backrun['signature']}")
        print(f"  Action: Bot sells token (profit taking)")
        print(f"  Token IN:  {backrun['token_in'][:16]}...")
        print(f"  Amount IN: {backrun['amount_in']:.6f}")
        print(f"  Token OUT: {backrun['token_out'][:16]}...")
        print(f"  Amount OUT: {backrun['amount_out']:.6f}")
        
        profit_data = calculate_sandwich_profit(sandwich)
        
        print(f"Bot strategy: {profit_data['strategy']}")
        print(f"Cost: {profit_data['cost']:.6f} {profit_data['cost_token']}")
        print(f"Revenue: {profit_data['revenue']:.6f} {profit_data['revenue_token']}")
        print(f"NET PROFIT: {profit_data['profit']:.6f} ({profit_data['profit_percent']:.2f}%)")
        print(f"Multi-slot span: {sandwich['slot_span']} slots")
        
        print("why is thsi a wide sandwich")
        print(f"1. Frontrun in slot {frontrun['slot']}")
        print(f"2. Victim in slot {victim['slot']} ({victim['slot'] - frontrun['slot']} slot(s) later)")
        print(f"3. Backrun in slot {backrun['slot']} ({backrun['slot'] - frontrun['slot']} slots after frontrun)")
        print(f"4. Total span: {sandwich['slot_span']} slots (evades single-slot detectors)")
        print(f"5. Same bot address in frontrun + backrun")
        print(f"6. Opposite token directions (buy → sell)")
        
        simulations.append({
            'sandwich_id': i,
            'sandwich': sandwich,
            'profit_data': profit_data
        })
    
    return simulations


def calculate_sandwich_profit(sandwich):

    frontrun = sandwich['frontrun']
    backrun = sandwich['backrun']
    victim = sandwich['victim']
    
    SOL = "So11111111111111111111111111111111111111112"
    
    if frontrun['token_in'] == SOL and backrun['token_out'] == SOL:
        return {
            'strategy': 'SOL → Token → SOL',
            'cost': frontrun['amount_in'],
            'cost_token': 'SOL',
            'revenue': backrun['amount_out'],
            'revenue_token': 'SOL',
            'profit': backrun['amount_out'] - frontrun['amount_in'],
            'profit_percent': ((backrun['amount_out'] - frontrun['amount_in']) / frontrun['amount_in'] * 100) if frontrun['amount_in'] > 0 else 0
        }
    
    elif frontrun['token_out'] == SOL and backrun['token_in'] == SOL:
        return {
            'strategy': 'Token → SOL → Token',
            'cost': backrun['amount_in'],
            'cost_token': 'SOL',
            'revenue': frontrun['amount_out'],
            'revenue_token': 'SOL',
            'profit': frontrun['amount_out'] - backrun['amount_in'],
            'profit_percent': ((frontrun['amount_out'] - backrun['amount_in']) / backrun['amount_in'] * 100) if backrun['amount_in'] > 0 else 0
        }
    
    else:
        token_bought = frontrun['amount_out']
        token_sold = backrun['amount_in']
        
        return {
            'strategy': 'Token-based sandwich',
            'cost': frontrun['amount_in'],
            'cost_token': frontrun['token_in'][:16] + '...',
            'revenue': backrun['amount_out'],
            'revenue_token': backrun['token_out'][:16] + '...',
            'profit': backrun['amount_out'] - frontrun['amount_in'],
            'profit_percent': ((backrun['amount_out'] - frontrun['amount_in']) / frontrun['amount_in'] * 100) if frontrun['amount_in'] > 0 else 0
        }


def generate_hypothetical_simulation():

    print(f"hypothetical sandwich attack simulate")
    print(f"\n User wants to swap 1 SOL for TOKEN_X")
    print(f"Bot detects pending transaction and executes wide sandwich\n")
    
    victim_amount = 1.0  # this is sol
    token_price_initial = 1000  # tokens per SOL
    
    print(f"[slot 1000] MARKET STATE:")
    print(f"  Token price: {token_price_initial} TOKEN_X per SOL")
    print(f"  Liquidity pool: Balanced")
    
    bot_frontrun_amount = 0.5 
    bot_tokens_bought = 500
    price_after_frontrun = 950
    
    print(f"\n[slot 1000] BOT FRONTRUN:")
    print(f"  Bot buys: {bot_tokens_bought} TOKEN_X")
    print(f"  Cost: {bot_frontrun_amount} SOL")
    print(f"  NEW price: {price_after_frontrun} TOKEN_X per SOL (inflated)")
    
    victim_tokens = victim_amount * price_after_frontrun
    expected_tokens = victim_amount * token_price_initial
    slippage_loss = expected_tokens - victim_tokens
    
    print(f"\n[slot 1001] VICTIM TRANSACTION:")
    print(f"  User buys TOKEN_X")
    print(f"  Pays: {victim_amount} SOL")
    print(f"  Expected: {expected_tokens} tokens")
    print(f"  Actual: {victim_tokens} tokens")
    print(f"  SLIPPAGE LOSS: {slippage_loss} tokens ({(slippage_loss/expected_tokens)*100:.2f}%)")
    
    price_after_victim = 1050
    bot_backrun_revenue = (bot_tokens_bought / price_after_victim) * price_after_victim
    bot_backrun_sol = bot_frontrun_amount * 1.1 
    
    print(f"\n[SLOT 1004] BOT BACKRUN (3 SLOTS LATER - WIDE):")
    print(f"  Bot sells: {bot_tokens_bought} TOKEN_X")
    print(f"  Receives: {bot_backrun_sol} SOL")
    print(f"  Price recovered to: {price_after_victim} TOKEN_X per SOL")
    
    bot_profit = bot_backrun_sol - bot_frontrun_amount
    profit_percent = (bot_profit / bot_frontrun_amount) * 100
    
    print(f"\nBot Performance:")
    print(f"  Initial capital: {bot_frontrun_amount} SOL")
    print(f"  Final capital: {bot_backrun_sol} SOL")
    print(f"  NET PROFIT: {bot_profit} SOL ({profit_percent:.2f}%)")
    
    print(f"\nVictim Impact:")
    print(f"  Expected tokens: {expected_tokens}")
    print(f"  Actual tokens: {victim_tokens}")
    print(f"  Loss: {slippage_loss} tokens")
    print(f"  Value extracted by bot: ~{bot_profit} SOL")
    
    print(f"\nWhy Wide Sandwich Works:")
    print(f" Slot 1000: Bot inflates price")
    print(f" Slot 1001: Victim buys at worse price")
    print(f" Slot 1004: Bot sells after 3 slots (EVADES DETECTION)")
    print(f" Single-slot detectors miss this pattern")
    print(f" Bot appears as normal trader, not attacker")
    
    return {
        'scenario': 'Hypothetical Wide Sandwich',
        'victim_loss_tokens': slippage_loss,
        'bot_profit_sol': bot_profit,
        'slot_span': 4,
        'detection_evasion': 'Multi-slot execution evades single-slot MEV detectors'
    }


def main():
    simulations = find_wide_sandwiches([])
    
    if simulations:
        with open('simulations.json', 'w') as f:
            json.dump(simulations, f, indent=2)
        
        print(f"Saved {len(simulations)} wide sandwich simulations to simulations.json")
    
    hypothetical = generate_hypothetical_simulation()
    
    with open('hypothetical_simulation.json', 'w') as f:
        json.dump(hypothetical, f, indent=2)
    
    print(f"  1. sandwich_simulations.json (real on-chain examples)")
    print(f"  2. hypothetical_simulation.json (bot strategy demonstration)")
    print(f"\nBoth files show WIDE (multi-slot) sandwich attacks")
    print(f"Slot spans: 2-8 slots (evading single-slot detectors)\n")


if __name__ == "__main__":
    main()