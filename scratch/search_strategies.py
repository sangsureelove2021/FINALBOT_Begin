import os
import re

strategies = ["compression_breakout", "triple_confluence", "macd_crossover", "rsi_reversal", "stochastic_crossover", "bb_rsi_confluence", "ema_crossover"]
root_dir = "c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT"

print("Scanning for strategy mentions in python files...")
for dirpath, _, filenames in os.walk(root_dir):
    if ".venv" in dirpath or ".git" in dirpath or "__pycache__" in dirpath:
        continue
    for filename in filenames:
        if filename.endswith(".py"):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                found = []
                for s in strategies:
                    if s in content:
                        found.append(s)
                if found:
                    print(f"File: {os.path.relpath(filepath, root_dir)}")
                    for s in found:
                        # find line numbers
                        lines = content.splitlines()
                        matching_lines = [i+1 for i, line in enumerate(lines) if s in line]
                        print(f"  - {s}: lines {matching_lines[:5]}")
            except Exception as e:
                pass
