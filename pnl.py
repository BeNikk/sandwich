import json
import utils

def calculate_sandwich_profit(sandwich):
    try:
        frontrun = sandwich['frontrun']
        backrun = sandwich['backrun']
        victim = sandwich['victim']
        
        base_token = frontrun['token_in']
        
        if base_token == backrun['token_out']:
            cost = frontrun['amount_in']
            revenue = backrun['amount_out']     
            
            profit = revenue - cost
            profit_percent = (profit / cost * 100) if cost > 0 else 0
            
            is_profitable = profit > 0
            
            victim_spent = victim['amount_in']
            
            return {
                'base_token': base_token,
                'base_token_name': utils.get_token_name(base_token),
                'cost': cost,
                'revenue': revenue,
                'profit': profit,
                'profit_percent': profit_percent,
                'is_profitable': is_profitable,
                'victim_spent': victim_spent,
                'extraction_rate': (profit / victim_spent * 100) if victim_spent > 0 else 0,
                'slot_span': sandwich['slot_span'],
                'bot_address': sandwich['bot_address']
            }
        
        return None
        
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
    
    results.sort(key=lambda x: x['profit_data']['profit'], reverse=True)
    
    profitable = [r for r in results if r['profit_data']['is_profitable']]
    unprofitable = [r for r in results if not r['profit_data']['is_profitable']]
    
    print(f"   Total analyzed: {len(results)}")
    print(f"   Profitable: {len(profitable)}")
    print(f"   Unprofitable: {len(unprofitable)}")
    
    if profitable:
        total_profit = sum(r['profit_data']['profit'] for r in profitable)
        avg_profit = total_profit / len(profitable)
        print(f"   Total profit extracted: {total_profit:.6f} SOL")
        print(f"   Average profit per sandwich: {avg_profit:.6f} SOL")
    
    return results, profitable, unprofitable


def display_top_sandwiches(profitable_sandwiches, top_n=5):
    print("Profitable sandwiches data")
    top_sandwiches = []
    
    for i, item in enumerate(profitable_sandwiches[:top_n], 1):
        sandwich = item['sandwich']
        profit = item['profit_data']
        
        print(f"#{i} | Bot: {profit['bot_address'][:16]}...")
        print(f"Profit: {profit['profit']:.6f} {profit['base_token_name']} ({profit['profit_percent']:.2f}%)")
        print(f"")
        print(f"   Cost (Front-run):     {profit['cost']:.6f} {profit['base_token_name']}")
        print(f"   Revenue (Back-run):   {profit['revenue']:.6f} {profit['base_token_name']}")
        print(f"   Victim spent:         {profit['victim_spent']:.6f}")
        print(f"   Extraction rate:      {profit['extraction_rate']:.2f}% of victim's trade")
        print(f"")
        print(f"   Slot span: {profit['slot_span']} slots")
        print(f"   Front-run slot: {sandwich['frontrun']['slot']}")
        print(f"   Victim slot:    {sandwich['victim']['slot']}")
        print(f"   Back-run slot:  {sandwich['backrun']['slot']}")
        print(f"")
        print(f"   Front: {sandwich['frontrun']['signature']}")
        print(f"   Victim: {sandwich['victim']['signature']}")
        print(f"   Back:  {sandwich['backrun']['signature']}")
        print(f"")
        
        top_sandwiches.append(item)
    
    return top_sandwiches


def generate_profit_summary(all_results, profitable, unprofitable):
    summary = {
        'total_sandwiches': len(all_results),
        'profitable_count': len(profitable),
        'unprofitable_count': len(unprofitable),
        'success_rate': (len(profitable) / len(all_results) * 100) if all_results else 0,
    }
    
    if profitable:
        profits = [r['profit_data']['profit'] for r in profitable]
        summary.update({
            'total_profit_extracted': sum(profits),
            'average_profit': sum(profits) / len(profits),
            'max_profit': max(profits),
            'min_profit': min(profits),
            'avg_slot_span': sum(r['profit_data']['slot_span'] for r in profitable) / len(profitable)
        })
    
    bot_profits = {}
    for r in profitable:
        bot = r['profit_data']['bot_address']
        if bot not in bot_profits:
            bot_profits[bot] = {'count': 0, 'total_profit': 0}
        bot_profits[bot]['count'] += 1
        bot_profits[bot]['total_profit'] += r['profit_data']['profit']
    
    top_bots = sorted(bot_profits.items(), key=lambda x: x[1]['total_profit'], reverse=True)[:3]
    summary['top_bots'] = [
        {
            'address': bot,
            'sandwich_count': data['count'],
            'total_profit': data['total_profit'],
            'avg_profit': data['total_profit'] / data['count']
        }
        for bot, data in top_bots
    ]
    
    return summary


def print_summary(summary):
    print(f"summary")
    
    print(f"Overall Statistics:")
    print(f"   Total sandwiches analyzed: {summary['total_sandwiches']}")
    print(f"   Profitable attacks: {summary['profitable_count']} ({summary['success_rate']:.1f}%)")
    print(f"   Unprofitable attacks: {summary['unprofitable_count']}")
    
    if summary.get('total_profit_extracted'):
        print(f"\n Profits:")
        print(f"   Total value extracted: {summary['total_profit_extracted']:.6f} SOL")
        print(f"   Average profit/sandwich: {summary['average_profit']:.6f} SOL")
        print(f"   Largest single profit: {summary['max_profit']:.6f} SOL")
        print(f"   Smallest profit: {summary['min_profit']:.6f} SOL")
        print(f"   Average slot span: {summary['avg_slot_span']:.1f} slots")
    
    if summary.get('top_bots'):
        print(f"\n Top Bots by Total Profit:")
        for i, bot in enumerate(summary['top_bots'], 1):
            print(f"   #{i}. {bot['address'][:16]}...")
            print(f"       Sandwiches: {bot['sandwich_count']}")
            print(f"       Total profit: {bot['total_profit']:.6f} SOL")
            print(f"       Avg profit: {bot['avg_profit']:.6f} SOL")


def main():
    try:
        with open('sandwich_attacks.json', 'r') as f:
            sandwiches = json.load(f)
    except FileNotFoundError:
        print("Error: sandwich_attacks.json not found. Run sandwich detection first!")
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
    
    print(f"\n Detailed analysis saved to profit_analysis.json")
    
    return top_5, summary


if __name__ == "__main__":
    main()