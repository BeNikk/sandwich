import json

def generate_verification_report():
    with open('sandwich_attacks.json', 'r') as f:
        sandwiches = json.load(f)
    
    for i, sandwich in enumerate(sandwiches[:3], 1):
        print(f"Bot: {sandwich['bot_address']}")
        print(f"Slot span: {sandwich['slot_span']} slots")
        
        print(f"\n Solscan Verification Links:")
        print(f"Front-run:  https://solscan.io/tx/{sandwich['frontrun']['signature']}")
        print(f"Victim:     https://solscan.io/tx/{sandwich['victim']['signature']}")
        print(f"Back-run:   https://solscan.io/tx/{sandwich['backrun']['signature']}")
        print(f"Bot wallet: https://solscan.io/account/{sandwich['bot_address']}")
    
    verification_data = {
        'total_sandwiches': len(sandwiches),
        'verified_samples': sandwiches[:3],
        'verification_instructions': [
            "1. Click each Solscan link above",
            "2. Verify slot numbers match",
            "3. Confirm bot wallet address is same",
            "4. Check token pair consistency",
            "5. Document any discrepancies"
        ]
    }
    
    with open('verification_report.json', 'w') as f:
        json.dump(verification_data, f, indent=2)

if __name__ == "__main__":
    generate_verification_report()