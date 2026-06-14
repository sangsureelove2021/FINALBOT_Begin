import subprocess
import time
import os
import json
import sys

# Change settings.json to Ai_BOT mode
settings_path = "config/settings.json"
with open(settings_path, "r") as f:
    settings = json.load(f)
original_mode = settings["account"]["trading_mode"]
print(f"Original mode: {original_mode}")
settings["account"]["trading_mode"] = "Ai_BOT"
with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
print("Changed to Ai_BOT mode")

# Run runner.py for 30 seconds
proc = subprocess.Popen([sys.executable, "runner.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(30)
proc.terminate()
time.sleep(2)
proc.kill()
out, err = proc.communicate()
print("=== RUNNER OUT ===")
print(out)
print("=== RUNNER ERR ===")
print(err)

# Check logs/pending_signals.json
pending_path = "logs/pending_signals.json"
if os.path.exists(pending_path):
    with open(pending_path, "r") as f:
        signals = json.load(f)
    print(f"Found pending_signals.json with {len(signals)} signals")
    if signals:
        print("First signal:", json.dumps(signals[0], indent=2)[:500])
        ai_actions = [s.get("ai_action") for s in signals]
        print(f"AI actions: {set(ai_actions)}")
        if "AI_PENDING" in ai_actions:
            print("SUCCESS: AI mode wrote signals with ai_action='AI_PENDING'")
        else:
            print("FAIL: No AI_PENDING found")
    else:
        print("No signals written")
else:
    print("pending_signals.json not found")

# Restore original mode
settings["account"]["trading_mode"] = original_mode
with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
print(f"Restored mode to {original_mode}")
