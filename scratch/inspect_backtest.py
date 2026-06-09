import json

file_path = r"C:\Users\Administrator\Downloads\TEST\backtest_with_outcomes.json"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Total entries in backtest_with_outcomes.json: {len(data)}")
    if len(data) > 0:
        first = data[0]
        print("First Entry Keys:", list(first.keys()))
        print("First Entry Sample:")
        print(json.dumps(first, indent=2)[:800])
except Exception as e:
    print("Error:", e)
