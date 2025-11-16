import json

def get_token_name(token_mint):
    token_map = {
        'So11111111111111111111111111111111111111112': 'SOL',
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC',
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT',
    }
    return token_map.get(token_mint, token_mint[:8] + '...')


def calculate_sandwich_profit(sandwich):
    #Calculate sandwich profit ONLY in SOL terms as normal tokens might not be valuable and can be pumped and dumped
    try:
        frontrun = sandwich['frontrun']
        backrun = sandwich['backrun']
        victim = sandwich['victim']
        
        SOL_MINT = "So11111111111111111111111111111111111111112"
        
        if frontrun['token_in'] == SOL_MINT:
            sol_spent = frontrun['amount_in']     
            sol_received = backrun['amount_out']   
            
            profit_sol = sol_received - sol_spent
            profit_percent = (profit_sol / sol_spent * 100) if sol_spent > 0 else 0
            
            return {
                'sandwich_type': 'SOL_ENTRY',
                'sol_spent': sol_spent,
                'sol_received': sol_received,
                'profit_sol': profit_sol,
                'profit_percent': profit_percent,
                'is_profitable': profit_sol > 0,
                'victim_spent_sol': victim['amount_in'] if victim['token_in'] == SOL_MINT else 0,
                'slot_span': sandwich['slot_span'],
                'bot_address': sandwich['bot_address']
            }
        
        elif frontrun['token_out'] == SOL_MINT:
            sol_received_frontrun = frontrun['amount_out']  # SOL from selling token
            sol_spent_backrun = backrun['amount_in']        # SOL to buy token back
            
            net_sol = sol_received_frontrun - sol_spent_backrun
            
            profit_percent = (net_sol / sol_spent_backrun * 100) if sol_spent_backrun > 0 else 0
            
            return {
                'sandwich_type': 'TOKEN_ENTRY',
                'sol_received': sol_received_frontrun,
                'sol_spent': sol_spent_backrun,
                'profit_sol': net_sol,
                'profit_percent': profit_percent,
                'is_profitable': net_sol > 0,
                'victim_spent_sol': victim['amount_in'] if victim['token_in'] == SOL_MINT else 0,
                'slot_span': sandwich['slot_span'],
                'bot_address': sandwich['bot_address'],
                'note': 'Bot sold token for SOL, then bought back. Net SOL change measured.'
            }
        
        else:
            return {
                'sandwich_type': 'NO_SOL',
                'profit_sol': 0,
                'is_profitable': False,
                'note': 'Cannot calculate profit - no SOL in transaction pair',
                'bot_address': sandwich['bot_address'],
                'slot_span': sandwich['slot_span']
            }
        
    except Exception as e:
        print(f"Error calculating profit: {e}")
        return None


def analyze_all_sandwiches(sandwiches):
    
    results = []
    
    for i, sandwich in enumerate(sandwiches):
        profit_data = calculate_sandwich_profit(sandwich)
        
        if profit_data:
            results.append({
                'sandwich_id': i + 1,
                'sandwich': sandwich,
                'profit_data': profit_data
            })
    
    results.sort(key=lambda x: x['profit_data']['profit_sol'], reverse=True)
    
    profitable = [r for r in results if r['profit_data']['is_profitable']]
    unprofitable = [r for r in results if not r['profit_data']['is_profitable']]
    
    print(f"   Total analyzed: {len(results)}")
    print(f"   Profitable (in SOL): {len(profitable)}")
    print(f"   Unprofitable: {len(unprofitable)}")
    
    if profitable:
        total_profit_sol = sum(r['profit_data']['profit_sol'] for r in profitable)
        avg_profit_sol = total_profit_sol / len(profitable)
        print(f"   Total SOL extracted: {total_profit_sol:.6f} SOL")
        print(f"   Average profit: {avg_profit_sol:.6f} SOL per sandwich")
    else:
        print(f"No profitable sandwiches found!")
    
    return results, profitable, unprofitable


def display_top_sandwiches(profitable_sandwiches, top_n=5):
    
    if not profitable_sandwiches:
        print(f"\n No profitable sandwiches to display")
        return []
    
    print(f"top {min(top_n, len(profitable_sandwiches))} most profitable sandwiches")
    
    top_sandwiches = []
    
    for i, item in enumerate(profitable_sandwiches[:top_n], 1):
        sandwich = item['sandwich']
        profit = item['profit_data']
        
        print(f"#{i} | Bot: {profit['bot_address'][:16]}...")
        print(f"Profit: {profit['profit_sol']:.6f} SOL ({profit['profit_percent']:.2f}%)")
        print(f"")
        
        if profit['sandwich_type'] == 'SOL_ENTRY':
            print(f"Bot's Trade (SOL Entry):")
            print(f"   Spent:    {profit['sol_spent']:.6f} SOL (front-run)")
            print(f"   Received: {profit['sol_received']:.6f} SOL (back-run)")
            print(f"   Profit:   {profit['profit_sol']:.6f} SOL")
        else:
            print(f"Bot's Trade (Token Entry):")
            print(f"   Received: {profit['sol_received']:.6f} SOL (front-run sell)")
            print(f"   Spent:    {profit['sol_spent']:.6f} SOL (back-run buy)")
            print(f"   Net SOL:  {profit['profit_sol']:.6f} SOL")
        
        if profit.get('victim_spent_sol', 0) > 0:
            extraction_rate = (profit['profit_sol'] / profit['victim_spent_sol'] * 100)
            print(f"")
            print(f"Victim Impact:")
            print(f"   Victim spent: {profit['victim_spent_sol']:.6f} SOL")
            print(f"   Extracted:    {extraction_rate:.2f}% of victim's trade")
        
        print(f"")
        print(f"Execution:")
        print(f"   Slot span:    {profit['slot_span']} slots")
        print(f"   Front slot:   {sandwich['frontrun']['slot']}")
        print(f"   Victim slot:  {sandwich['victim']['slot']}")
        print(f"   Back slot:    {sandwich['backrun']['slot']}")
        
        print(f"")
        print(f"Transactions:")
        print(f"   Front:  {sandwich['frontrun']['signature']}")
        print(f"   Victim: {sandwich['victim']['signature']}")
        print(f"   Back:   {sandwich['backrun']['signature']}")
        print(f"\n")
        
        top_sandwiches.append(item)
    
    return top_sandwiches


def generate_profit_summary(all_results, profitable, unprofitable):
    
    summary = {
        'total_sandwiches': len(all_results),
        'profitable_count': len(profitable),
        'unprofitable_count': len(unprofitable),
        'success_rate_percent': (len(profitable) / len(all_results) * 100) if all_results else 0,
    }
    
    if profitable:
        profits_sol = [r['profit_data']['profit_sol'] for r in profitable]
        summary.update({
            'total_sol_extracted': sum(profits_sol),
            'average_profit_sol': sum(profits_sol) / len(profits_sol),
            'max_profit_sol': max(profits_sol),
            'min_profit_sol': min(profits_sol),
            'avg_slot_span': sum(r['profit_data']['slot_span'] for r in profitable) / len(profitable)
        })
        
        bot_profits = {}
        for r in profitable:
            bot = r['profit_data']['bot_address']
            if bot not in bot_profits:
                bot_profits[bot] = {'count': 0, 'total_profit_sol': 0}
            bot_profits[bot]['count'] += 1
            bot_profits[bot]['total_profit_sol'] += r['profit_data']['profit_sol']
        
        top_bots = sorted(bot_profits.items(), key=lambda x: x[1]['total_profit_sol'], reverse=True)[:3]
        summary['top_bots'] = [
            {
                'address': bot,
                'sandwich_count': data['count'],
                'total_profit_sol': data['total_profit_sol'],
                'avg_profit_sol': data['total_profit_sol'] / data['count']
            }
            for bot, data in top_bots
        ]
    
    return summary


def print_summary(summary):
    
    print(f" Profit (sol based)")
    print(f"   Total sandwiches: {summary['total_sandwiches']}")
    print(f"   Profitable: {summary['profitable_count']} ({summary['success_rate_percent']:.1f}%)")
    print(f"   Unprofitable: {summary['unprofitable_count']}")
    
    if summary.get('total_sol_extracted') is not None:
        print(f"   Total SOL extracted: {summary['total_sol_extracted']:.6f} SOL")
        print(f"   Average profit: {summary['average_profit_sol']:.6f} SOL per sandwich")
        print(f"   Largest profit: {summary['max_profit_sol']:.6f} SOL")
        print(f"   Smallest profit: {summary['min_profit_sol']:.6f} SOL")
        print(f"   Avg slot span: {summary['avg_slot_span']:.1f} slots")
        
        sol_price = 150  # Hardcoded/apporoximate
        total_usd = summary['total_sol_extracted'] * sol_price
        print(f"\nEstimated USD Value:")
        print(f"   Total extracted: ~${total_usd:.2f} USD (at ${sol_price}/SOL)")
    
    if summary.get('top_bots'):
        print(f"\nTop Bots by Profit:")
        for i, bot in enumerate(summary['top_bots'], 1):
            print(f"   #{i}. {bot['address'][:16]}...")
            print(f"       Sandwiches: {bot['sandwich_count']}")
            print(f"       Total profit: {bot['total_profit_sol']:.6f} SOL")
            print(f"       Avg profit: {bot['avg_profit_sol']:.6f} SOL")


def main():
    try:
        with open('sandwich_attacks.json', 'r') as f:
            sandwiches = json.load(f)
    except FileNotFoundError:
        print("sandwich_attacks.json not found!")
        print("Run sandwich detection first: python3 app.py")
        return
    
    all_results, profitable, unprofitable = analyze_all_sandwiches(sandwiches)
    
    top_5 = display_top_sandwiches(profitable, top_n=5)
    
    summary = generate_profit_summary(all_results, profitable, unprofitable)
    print_summary(summary)
    
    output = {
        'summary': summary,
        'top_5_sandwiches': top_5,
        'all_profitable': profitable,
        'unprofitable': unprofitable
    }
    
    with open('profit_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f" Detailed analysis saved to profit_analysis.json")
    
    return top_5, summary


if __name__ == "__main__":
    main()
