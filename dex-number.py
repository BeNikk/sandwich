import json
with open('dex_transactions.json', 'r') as f:
    data = json.load(f)
    print(len(data))

with open('sandwich_attacks.json', 'r') as f:
    data = json.load(f)
    print(len(data))